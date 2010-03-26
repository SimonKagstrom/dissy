#!/usr/bin/python

import sys
import os.path
projdir = os.path.normpath(os.path.join(os.path.dirname(sys.argv[0]), '.'))
sys.path = [projdir] + sys.path

import unittest

import dissy.constdom
from dissy.constdom import ConstDom
import wali

class TestConstDom(unittest.TestCase):

    def test_basic(self):
        a = ConstDom("")
        self.assertEqual(str(a), "{ }")

        a = ConstDom("r1 = 5")
        self.assertEqual(str(a), "{ r1 = 5 ; }")
        b = ConstDom("r2 = 7")
        self.assertEqual(str(b), "{ r2 = 7 ; }")

        c = ConstDom("r1 = 5; r2 = 7")
        self.assertEqual(str(c), "{ r1 = 5 ; r2 = 7 ; }")

        d = ConstDom("r2 = r2 + 5")
        self.assertEqual(str(d), "{ r2 = r2 + 5 ; }")

        self.assertEqual(wali.getKey('*'), wali.getEpsilonKey())

    def test_extend(self):
        a = ConstDom("r1 = 5")
        b = ConstDom("r2 = 7")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r1 = 5 ; r2 = 7 ; }")

        a = ConstDom("r1 = 5")
        b = ConstDom("r2 = r1 + 2")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r1 = 5 ; r2 = (5) + 2 ; }")

        a = ConstDom("r1 = 5; r2 = 7")
        b = ConstDom("r3 = r1 + r2")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r1 = 5 ; r2 = 7 ; r3 = (5) + (7) ; }")

        a = ConstDom("r1 = 5; r2 = 7")
        b = ConstDom("r3 = r1 + r2")
        c = b.extend(a)
        self.assertEqual(str(c), "{ r1 = 5 ; r2 = 7 ; r3 = r1 + r2 ; }")


        a = ConstDom("")
        b = ConstDom("r2 = r1 + 5")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r2 = r1 + 5 ; }")
        b = ConstDom("r3 = r2 + 5")
        c = c.extend(b)
        self.assertEqual(str(c), "{ r2 = r1 + 5 ; r3 = (r1 + 5) + 5 ; }")
        a = ConstDom("")
        b = ConstDom("r2 = r2 + 5")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r2 = r2 + 5 ; }")

        #Extend with same value
        a = ConstDom("r2 = 5")
        b = ConstDom("r2 = 5")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r2 = 5 ; }")

        #extend with unknown value
        a = ConstDom("r2 = 5")
        b = ConstDom("r2 = top")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r2 = top ; }")

        #extend unknown with known value
        a = ConstDom("r2 = top")
        b = ConstDom("r2 = 5")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r2 = 5 ; }")

        #test syntactic substitution bugs
        a = ConstDom("r1 = 1 ; r12 = 4")
        b = ConstDom("r2 = r1 + r12")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r1 = 1 ; r2 = (1) + (4) ; r12 = 4 ; }")

        a = ConstDom("r0 = 1 ; r1 = 2")
        b = ConstDom("r1 = r0")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r0 = 1 ; r1 = (1) ; }")

        a = ConstDom("r13 = r13 - 4")
        b = ConstDom("r13 = r13 - 4")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r13 = (r13 - 4) - 4 ; }")

        a = ConstDom("r0 = 30 ; r13 = (r13 - 4) - 4 ; r14 = top")
        b = ConstDom("r0 = top ; r13 = (r13 - 4) + 4 ; r14 = top")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r0 = top ; r13 = (((r13 - 4) - 4) - 4) + 4 ; r14 = top ; }")

        a = ConstDom("r13 = r13 - 4 ; r14 = top")
        b = ConstDom("r0 = top")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r0 = top ; r13 = r13 - 4 ; r14 = top ; }")

        a = ConstDom("r13 = r13 - 4 ; r14 = r13 + 8")
        b = ConstDom("r0 = top")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r0 = top ; r13 = r13 - 4 ; r14 = r13 + 8 ; }")

        a = ConstDom("r13 = r13 - 4 ; r14 = top")
        b = ConstDom("r13 = r13 + 4")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r13 = (r13 - 4) + 4 ; r14 = top ; }")

        a = ConstDom("r1 = 0")
        b = ConstDom("r13 = r13 - 12")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r1 = 0 ; r13 = r13 - 12 ; }")

        a = ConstDom("r0 = 67164")
        b = ConstDom("r5 = r0")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r0 = 67164 ; r5 = (67164) ; }")

        a = ConstDom("r0 = 67164")
        b = ConstDom("r5 = (r0) + 40")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r0 = 67164 ; r5 = ((67164)) + 40 ; }")

        a = ConstDom("r13 = r13 - 16")
        b = ConstDom("r13 = r13 + 16")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r13 = (r13 - 16) + 16 ; }")


        a = ConstDom("r1 = top ; r13 = r13 - 16")
        b = ConstDom("r13 = r13 + 16")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r1 = top ; r13 = (r13 - 16) + 16 ; }")

        a = ConstDom("r5 = r0")
        b = ConstDom("r5 = r5 + 40")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r5 = (r0) + 40 ; }")


        #Substitution should only happen in one "level", e.g.
        #r5 + 40 => r0 + 40 =!=> top + 40
        a = ConstDom("r0 = top ; r5 = r0")
        b = ConstDom("r5 = r5 + 40")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r0 = top ; r5 = (r0) + 40 ; }")

        a = ConstDom("r0 = 4")
        b = ConstDom("r5 = r0")
        c = a.extend(b)
        self.assertEqual(str(c), "{ r0 = 4 ; r5 = (4) ; }")



    def test_0element(self):
        a = ConstDom("")
        z = a.zero()
        self.assertEqual(str(z), 
            "{ ZERO }")

        a = ConstDom("r1 = 3")
        #Test that zero is annihilator for extend, i.e.
        # a x Z = Z = Z x a
        b = a.extend(z)
        self.assertEqual(str(b), str(z))
        b = z.extend(a)
        self.assertEqual(str(b), str(z))

        #Test that zero is neutral for combine
        #Test with manual deref
        b = a.combine(z.__deref__())
        self.assertEqual(str(b), str(a))
        #Test with auto deref
        b = a.combine(z)
        self.assertEqual(str(b), str(a))

    def test_1element(self):
        a = ConstDom("")
        o = a.one()
        #self.assertEqual(str(o), 
        #    "{ ONE }")

        a = ConstDom("r1 = 3")
        #test that one is neutral for extend
        b = a.extend(o)
        self.assertEqual(str(b), str(a))
        b = o.extend(a)
        self.assertEqual(str(b), str(a))


    def test_combine(self):
        a = ConstDom("r1 = 5")
        b = ConstDom("r1 = 7")
        c = a.combine(b)
        self.assertEqual(str(c), "{ r1 = top ; }")

        a = ConstDom("r1 = 5")
        b = ConstDom("")
        c = a.combine(b)
        self.assertEqual(str(c), "{ r1 = top ; }")

        a = ConstDom("r1 = 5")
        b = ConstDom("r1 = 5")
        c = a.combine(b)
        self.assertEqual(str(c), "{ r1 = 5 ; }")
        
        a = ConstDom("r1 = 5; r2 = 7")
        b = ConstDom("r1 = 5; r2 = 8")
        c = a.combine(b)
        self.assertEqual(str(c), "{ r1 = 5 ; r2 = top ; }")
        
        a = ConstDom("r1 = 7; r2 = 5")
        b = ConstDom("r1 = 8; r2 = 5")
        c = a.combine(b)
        self.assertEqual(str(c), "{ r1 = top ; r2 = 5 ; }")
        
        a = ConstDom("r1 = 7; r2 = 5")
        b = ConstDom("r1 = 8; r2 = 4")
        c = a.combine(b)
        self.assertEqual(str(c), "{ r1 = top ; r2 = top ; }")

    def test_basicstack(self):
        a = ConstDom("r1 = 5 ; r2 = 7", "top")
        self.assertEqual(str(a), "{ r1 = 5 ; r2 = 7 ; } top")

        a = ConstDom("r1 = 5 ; r2 = 7", "")
        b = ConstDom("r1 = r1 + r2", "")
        push = ConstDom("", "push r1 ; r2")

        self.assertEqual(str(a.extend(b.extend(push))), 
            "{ r1 = (5) + (7) ; r2 = 7 ; } [push ((5) + (7)) ; (7) ; ]")
        self.assertEqual(str(a.extend(b).extend(push)), 
            "{ r1 = (5) + (7) ; r2 = 7 ; } [push ((5) + (7)) ; (7) ; ]")

        push1 = ConstDom("", "push r1")
        push2 = ConstDom("", "push r2")
        self.assertEqual(str(push1.extend(push2)), "{ } [push r1 ; r2 ; ]")

        pop1 = ConstDom("", "pop r1")
        pop2 = ConstDom("", "pop r2 ; r3")
        self.assertEqual(str(pop1.extend(pop2)), "{ } [pop r1 ; r2 ; r3 ; ]")



    def test_stackmanipulation(self):
        a = ConstDom("r1 = 5 ; r2 = 7")
        push = ConstDom("", "push r1 ; r2")
        f = ConstDom("r1 = 0 ; r2 = 0")
        pop = ConstDom("", "pop r2 ; r1")

        self.assertEqual(str(push), "{ } [push r1 ; r2 ; ]")
        self.assertEqual(str(pop), "{ } [pop r2 ; r1 ; ]")

        incall = a.extend(push)
        self.assertEqual(str(incall), "{ r1 = 5 ; r2 = 7 ; } [push (5) ; (7) ; ]")

        incall2 = a.extend(push).extend(f) 
        self.assertEqual(str(incall2), "{ r1 = 0 ; r2 = 0 ; } [push (5) ; (7) ; ]")

        totalexc = a.extend(push).extend(f).extend(pop)
        self.assertEqual(str(totalexc), "{ r1 = (5) ; r2 = (7) ; }")

    def test_basicweightdomain(self):
        a = ConstDom("")
        wali.test_semelem_impl(wali.SemElemPtr(a))
        
    def no_test_funccall(self):
        """
        n0: r1 = 30;
        n1: f();
        n2: r1 = 5;
        n6: f();
        n7: 

        n3: f():
        n4:    dostuff
        n5:    return
        """
        w = wali.WPDS()
        p = wali.getKey("p")
        accept = wali.getKey("accept")
        n = []
        for i in range(0, 8):
            n += [wali.getKey("n" + str(i))]
        z = wali.ConstDom().zero()

        noEffect = wali.SemElemPtr(wali.ConstDom(""))
        w.add_rule(p, n[0], p, n[1], wali.SemElemPtr(wali.ConstDom("r1 = 30")))
        w.add_rule(p, n[1], p, n[3], n[2], noEffect)
        w.add_rule(p, n[2], p, n[6], wali.SemElemPtr(wali.ConstDom("r1 = 5")))
        w.add_rule(p, n[6], p, n[3], n[7], noEffect)

        w.add_rule(p, n[3], p, n[4], wali.SemElemPtr(wali.ConstDom("r2 = 5")))
        w.add_rule(p, n[4], p, n[5], noEffect)
        w.add_rule(p, n[5], p, noEffect)

        print w

        query = wali.WFA()

        #q = wali.getKey("q")
        #query.addTrans( p, n[3] , q, noEffect);
        #query.addTrans( q, n[2] , accept, noEffect);
        
        query.addTrans( p, n[0] , accept, noEffect);
        query.set_initial_state( p )
        query.add_final_state( accept )
        query.setQuery(wali.WFA.REVERSE)

        print query

        print "============== ANSWER ==============="
        answer = wali.WFA()
        w.poststar(query, answer)
        print str(answer)
        compkey = wali.getKey(p, n[3])
        print wali.key2str(compkey)
        genkeysource = wali.GenKeySource(1, compkey)
        #print  genkeysource.to_string()
        genkey = wali.getKey( genkeysource )
        genkey = wali.getKey( genkeysource )

        print str(genkey)

        #for i in answer.asList():
        #    print wali.getKeySource(i.fromState()).toString(), \
        #        "==", \
        #        wali.getKeySource(i.stack()).toString(), \
        #        "=>", \
        #        wali.getKeySource(i.toState()).toString(), \
        #        "  ", \
        #        i.weight()
        #    #import pdb; pdb.set_trace()

        abemad = answer.match(genkey, n[2])

        #import pdb; pdb.set_trace()
        print abemad, dir(abemad)
        print

        mylist = abemad.asList()
        print len(mylist), mylist

        for i in mylist:
            print "abemad: ", i
            print "props: ", i.fromState(), i.stack(), i.toState(), i.weight(), i.getDelta()


        functionsummaries = answer.match(p, wali.getKey('*')).asList()
 
        functionsummary = functionsummaries[0]
        
        callsite = answer.match(p, n[5]).asList()[0]

        print callsite.weight(), functionsummary.weight()

        #i = abemad.begin()
        #print i, dir(i), i.__int__()

        #while i != abemad.end():
        #    print i
        #    #i++


    def no_test_all_loopbound_combinations(self):
        import valueanalysis
        self.assertEqual(list(valueanalysis.all_loopbound_combinations([])), [ () ])
        self.assertEqual(list(valueanalysis.all_loopbound_combinations([3])), [(0, ), (1, ), (2, )])
        self.assertEqual(list(valueanalysis.all_loopbound_combinations([3, 3])),
            [(0,0), (0,1), (0,2), (1,0), (1,1), (1,2), (2,0), (2,1), (2,2)])
        self.assertEqual(list(valueanalysis.all_loopbound_combinations([2, 2, 2])),
            [(0,0,0), (0,0,1), (0,1,0), (0,1,1), (1,0,0), (1,0,1), (1,1,0), (1,1,1)])


if __name__ == '__main__':
    unittest.main()
