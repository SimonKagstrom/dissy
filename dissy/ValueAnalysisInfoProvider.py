######################################################################
##
## Copyright (C) 2009,  Mads Chr. Olesen
##
## Author:        Mads Chr. Olesen <mads@mchro.dk>
## Description:   Value analysis info provider for the infobox
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################
from dissy.valueanalysis import *
import wali
import cgi

class ValueAnalysisInfoProvider:
    def __init__(self, filecontainer):
        self.filecontainer = filecontainer
        self.analysed = False
        self.arch = self.filecontainer.arch

    def denormalize_regname(self, i):
        denormalized = self.arch.denormalize_regname('r%d' % i)
        if denormalized != 'r%d' % i:
            return denormalized + ' (r%d)' % i
        return denormalized

    def analyse(self):
        #construct WPDS
        for func in self.filecontainer.getFunctions():
            if func.getInstructions() == []:
                func.parse()
                func.link()
        res = construct_wpds(self.filecontainer)

        print "Value Analysis: WPDS constructed"

        #Compute the result
        query = wali.WFA()
        p = wali.getKey("p")
        accept = wali.getKey("accept")
        #XXX configurable entrypoint
        initloc = wali.getKey("f_main")
        query.addTrans( p, initloc  , accept, getNoEffect() );
        query.set_initial_state( p )
        query.add_final_state( accept )
        self.answer = wali.WFA()
        res.poststar(query, self.answer)
        
        print "Value Analysis: post* calculated"

        #print self.answer

        #post-process the result
        self.calling_contexts = calculate_calling_contexts(self.filecontainer, self.answer)

        print "Value Analysis: calling contexts calculated"

        #self.mem_accesses = calculate_memaccesses(self.filecontainer, 
        #    self.calling_contexts, self.answer)
        #print self.mem_accesses
        self.analysed = True

    def getInstructionInfo(self, instruction):
        if not self.analysed:
            return ""
        if instruction.opcode == '.word':
            return ""

        #if instruction.address in self.mem_accesses:
        #    print instruction.address
        #    mem_access = self.mem_accesses[instruction.address]
        #    return "Memory access: " + str(mem_access)

        weight = calculate_weight(self.filecontainer, self.calling_contexts,
            self.answer, instruction)

        #Function has loops, but this instruction is only executed once
        if weight is None:
            return ""
        elif isinstance(weight, dict) and len(weight) == 1:
            weight = weight[weight.keys()[0]]

        def constdom_to_table(constdom, id=''):
            """
            Converts a ConstDom into a nice HTML table for viewing
            """
            vals = constdom.asList()
            regdict = dict(zip(
                map(lambda x: 'r'+str(x), range(0, len(vals))), 
                vals))
            rows = []
            i = 0
            for regval in vals:
                intval = "N/A"
                hexval = "N/A"
                if regval != "":
                    try:
                        intval = regval_from_value_exprs(regdict, 'r%d' % (i))
                        hexval = hex(long(intval))[:-1]
                    except Exception, e:
                        #print e
                        pass
                rows += ["<td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td>" % \
                    (self.denormalize_regname(i), intval, hexval, regval)]
                i += 1

            if rows:
                rows = [
                    "<td>%s</td> <td>%s</td> <td>%s</td> <td>%s</td>" % \
                        ("Reg.", "Value (dec.)", "Value (hex.)", "Value (symbolic)")
                    ] + rows
                return '<table class="valuetable" id="%s"><tr>' % (id) + ("</tr><tr>".join(rows)) + "</tr></table>"
            else:
                return ""
        
        def add_to_combined_vals(combined_vals, constdom):
            #print combined_vals
            i = 0
            for regval in constdom.asList():
                hexval = 'N/A'
                try:
                    intval = evaluate_regval(regval)
                    hexval = hex(long(intval))[:-1]
                except Exception, e:
                    #print e
                    pass

                combined_vals[i] += [hexval]
                #print combined_vals
                i += 1
            #print combined_vals
            #import pdb; pdb.set_trace()

        def combined_vals_to_table(combined_vals, id):
            rows = []
            i = 0
            for regvals in combined_vals:
                #if all are the same, just display that
                if len([x for x in regvals if x == regvals[0]]) == len(regvals):
                    rows += ["<td>%s</td> <td>%s</td>" % (self.denormalize_regname(i), regvals[0])]
                #if all but first are the same
                elif len([x for x in regvals[1:] if x == regvals[1]]) == len(regvals)-1:
                    rows += ["<td>%s</td> <td>%s</td>" % (self.denormalize_regname(i), 
                        regvals[0] + ", " + regvals[1] + ", ...")]
                #too many to display
                elif len(regvals) > 100:
                    rows += ["<td>%s</td> <td>%s...</td>" % (self.denormalize_regname(i),
                        ", ".join(regvals[:100]))]
                else:
                    rows += ["<td>%s</td> <td>%s</td>" % (self.denormalize_regname(i),
                        ", ".join(regvals))]
                i += 1

            if rows:
                rows = [
                    "<td>%s</td> <td>%s</td>" % \
                        ("Reg.", "Values (hex.)")
                    ] + rows

            return '<table class="valuetable" id="%s"><tr>' % (id) + \
                ("</tr><tr>".join(rows)) + \
                "</tr></table>"            
        
        #make viewing nicer
        if isinstance(weight, dict):
            tables = []
            options = []
            loop_contexts = weight.keys()
            loop_contexts.sort()

            #combined_vals = [[]] * len(weight[loop_contexts[0]].asList())
            combined_vals = [list() for x in weight[loop_contexts[0]].asList()]

            #display all, if less than 20
            if len(loop_contexts) <= 20:
                contextstodisplay = loop_contexts
            else: #display first 5 and last 5
                contextstodisplay = loop_contexts[:5] + ['...'] + loop_contexts[-5:]
            
            #First 100 are used for combined view
            for k in loop_contexts[:100]:
                add_to_combined_vals(combined_vals, weight[k])

            for k in contextstodisplay:
                if k == '...':
                    options += [('', '...')]
                    continue
                tableid = str(k).replace('(', '').replace(')', '').replace(',', '_').replace(' ', '')
                tablelabel = str(k).replace('(', '').replace(')', '').replace(' ', '')

                tables += [constdom_to_table(weight[k], 'valuetable' + tableid)]
                options += [(tableid, tablelabel)]
                
            tables = [combined_vals_to_table(combined_vals, 
                'valuetablecombined')] + tables
            
            strweight = """
                <script>
                function showTable(value) {
                    valuetables = document.getElementsByClassName('valuetable')
                    for (var j = 0; j < valuetables.length; j++) {
                        valuetables[j].style.display = 'none';
                    }
                    el = document.getElementById('valuetable' + value)
                    if (el) el.style.display = '';
                }
                </script>
                """ + \
                """<select onchange="showTable(this.options[this.selectedIndex].value);"
                    onkeyup="showTable(this.options[this.selectedIndex].value);">
                    <option value="combined">Combined</option>""" + \
                "".join(map(lambda x: "<option value='%s'>%s</option>" % x, options)) + \
                "</select><br />" + \
                "".join(tables) + \
                "<script>showTable('combined');</script>"
        else:
            strweight = '<br />' + constdom_to_table(weight)
            strweight += '<br />Stack contents: ' + str(weight.getStack())

        strweight = strweight + \
            "<br />Symbolic register effect: " + \
            self.arch.getInstructionEffect(instruction, instruction.function) + \
            "<br />Symbolic stack effect: " + \
            self.arch.getInstructionStackEffect(instruction, instruction.function)
        return strweight
