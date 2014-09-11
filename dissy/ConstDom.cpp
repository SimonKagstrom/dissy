/*!
 * @author Mads Chr. Olesen
 */

#include "ConstDom.hpp"

using namespace std;

#include <sstream>
#include <iostream>
#include <vector>
#include <iterator>

//#define CONSTDOM_DEBUG

// The max length of a weight, before it gets truncated to "top"
#define CONSTDOM_MAX_LEN 5000

template <class T>
bool string_to_num(T& t, 
                 const std::string& s, 
                 std::ios_base& (*f)(std::ios_base&))
{
  std::istringstream iss(s);
  return !(iss >> f >> t).fail();
}


void ConstDom::tokenize(const std::string& str,
                      std::vector<std::string>& tokens,
                      const std::string& delimiters)
{
    // Skip delimiters at beginning.
    string::size_type lastPos = str.find_first_not_of(delimiters, 0);
    // Find first "non-delimiter".
    string::size_type pos     = str.find_first_of(delimiters, lastPos);

    while (string::npos != pos || string::npos != lastPos)
    {
        // Found a token, add it to the vector.
        tokens.push_back(str.substr(lastPos, pos - lastPos));
        // Skip delimiters.  Note the "not_of"
        lastPos = str.find_first_not_of(delimiters, pos);
        // Find next "non-delimiter"
        pos = str.find_first_of(delimiters, lastPos);
    }
}

void TrimSpaces( string& str)  
{  
    // Trim Both leading and trailing spaces  
    size_t startpos = str.find_first_not_of(" \t"); // Find the first character position after excluding leading blank spaces  
    size_t endpos = str.find_last_not_of(" \t"); // Find the first character position from reverse af  
  
    // if all spaces or empty return an empty string  
    if(( string::npos == startpos ) || ( string::npos == endpos))  
    {  
        str = "";
    }  
    else  
        str = str.substr( startpos, endpos-startpos+1 );  
}

void find_and_replace( string &str, const string searchString, string replaceString ) {
  /*
  if (searchString == replaceString)
    std::cerr << "find_and_replace failed: " << searchString << " = " << replaceString << std::endl;
  assert( searchString != replaceString );
  */

  string::size_type pos = 0;
  while ( (pos = str.find(searchString, pos)) != string::npos ) {
      char trailingchar = str[pos + searchString.size()];
      //std::cerr << "Trailing char: " << trailingchar << std::endl;
      if (trailingchar < '0' || trailingchar > '9') {
        str.replace( pos, searchString.size(), replaceString );
        //std::cerr << "Proceeding with " << str << std::endl;
        pos = pos + replaceString.size();
      }
      else {
        std::cerr << "Ignored match " << (int)trailingchar << std::endl;
        pos = pos + 1;
      }
  }


}

ConstDom::ConstDom( ) :
isZero(false)
{
  //TODO
}


ConstDom::ConstDom( std::string val, std::string stackeffect ) :
isZero(false) , stackIsTop(false), stackIsNegative(false)
{
  if (val == "ZERO") {
    isZero = true;
    return;
  }
  //val is of the form rX = f(r1, ..., rN); rY = f(r1, ..., rN)
  vector<string> assignments;
  tokenize(val, assignments, ";");
  
  for (vector<string>::iterator i = assignments.begin(); 
        i != assignments.end(); i++) {

    TrimSpaces(*i);
    int regassign = 0;
    //Find first r
    string::size_type regnum_start = i->find_first_of("r", 0) + 1;
    //find next non-numeric
    string::size_type regnum_end = i->find_first_not_of("0123456789", 
                                                  regnum_start);

    if (!string_to_num<int>(regassign, i->substr(regnum_start, regnum_end), std::dec)) {
      //XXX fail
      continue;
    }
    vals[regassign] = i->substr(i->find_first_of("=", 0) + 1 );
    TrimSpaces(vals[regassign]);
    
  }

  if (stackeffect != "") {
    if (stackeffect == "top") {
      stack.clear();
      stackIsTop = true;
    }
    else if (stackeffect.substr(0, 4) == "push") {
      vector<string> registers;
      tokenize(stackeffect.substr(5), registers, ";");
    
      for (vector<string>::iterator i = registers.begin(); 
        i != registers.end(); i++) {

        TrimSpaces(*i);
        int regassign = 0;
        //Find first r
        string::size_type regnum_start = i->find_first_of("r", 0) + 1;
        //find next non-numeric
        string::size_type regnum_end = i->find_first_not_of("0123456789", 
                                                      regnum_start);
        if (!string_to_num<int>(regassign, i->substr(regnum_start, regnum_end), std::dec)) {
          //XXX fail
          continue;
        }
        
        std::string valtopush = vals[regassign];
        // if undef'ed, make identity
        if (valtopush == "") {
          valtopush = "r";
          valtopush.append(i->substr(regnum_start, regnum_end));
        }

        stack.push_back( valtopush );
      }
    }
    else if (stackeffect.substr(0, 3) == "pop") {
      stackIsNegative = true;
      vector<string> registers;
      tokenize(stackeffect.substr(4), registers, ";");
    
      for (vector<string>::iterator i = registers.begin(); 
        i != registers.end(); i++) {

        TrimSpaces(*i);
        //Find first r
        string::size_type regnum_start = i->find_first_of("r", 0) + 1;
        //find next non-numeric
        string::size_type regnum_end = i->find_first_not_of("0123456789", 
                                                      regnum_start);
        
        string regtopop = "r";
        regtopop.append(i->substr(regnum_start, regnum_end));
        stack.push_back( regtopop );
      }
    }
  }
}

ConstDom::~ConstDom()
{
  //std::cerr << "~ConstDom()   :" << numConstDomes << std::endl;
}

sem_elem_t ConstDom::one() const
{  
  static sem_elem_t O(new ConstDom("ONE"));
  return O;
}

sem_elem_t ConstDom::zero() const
{
  static sem_elem_t Z = new ConstDom("ZERO");
  return Z;
}


std::string extendSingle(std::string cur, std::string vals[CONSTDOM_NUM_REGS]) {
  // Go through the string, in succession, and replace all occurences
  // of rX with the previous value
  string::size_type pos = 0;

  std::string collected_regname = "";
  while (pos <= cur.length())
  {
    //std::cerr << "string: " << cur << std::endl;
    //std::cerr << pos << "/" << cur.length() << std::endl;

    // Start of regname
    if (cur[pos] == 'r') {
      assert(collected_regname == "");
      collected_regname += 'r';
    }
    // continuation of regname
    else if (cur[pos] >= '0' && cur[pos] <= '9' && collected_regname != "") {
      collected_regname += cur[pos];
    }
    else {
      if (collected_regname != "") { //Do substitution

        int j;
        if (!string_to_num<int>(j, collected_regname.substr(1), std::dec)) {
          assert(false);
        }

        //Previously computed value
        if (!vals[j].empty() && vals[j] != "top") {
          std::string replaceString = "(" + vals[j] + ")";
          cur.replace( pos - collected_regname.size(), collected_regname.size(), 
            "(" + vals[j] + ")" );
          pos = pos + replaceString.size() - 1;
          
          //std::cerr << "After replace: " << cur << std::endl;
        // Value unchanged until now
        } else if (vals[j].empty()) {

        //Uses unknown value
        } else {
          cur = "top";
          pos = cur.length() - 1; //bail out
        }
        collected_regname = "";
      }
    }
    pos += 1;
  }

  //String too long?
  if (cur.length() > CONSTDOM_MAX_LEN)
    cur = "top";

  return cur;
}

sem_elem_t ConstDom::extend( SemElem* se )
{
  // Extend is called "sequentially" for each node, given its
  // "predecessor"
  ConstDom* rhs = static_cast< ConstDom* >(se);
  std::ostringstream out;
  std::string cur;

#ifdef CONSTDOM_DEBUG
  std::cerr << "Extend called for ";
  print(std::cerr);
  std::cerr << " ";
  rhs->print(std::cerr);
#endif

  // zero is the annihilator for extend
  if (isZero || rhs->isZero) {
    //std::cerr << "Extend zero-annihilated" << std::endl;
    return zero();
  }

  // Extend each register's expression
  for (int i = 0; i < CONSTDOM_NUM_REGS; i++) {
    // prefer if rhs has def
    if (!rhs->vals[i].empty())
    {
      cur = std::string(rhs->vals[i]);
      cur = extendSingle(cur, vals);
    }
    // if lhs has def
    else if (!vals[i].empty())
      cur = std::string(vals[i]);
    //Both empty
    else
      continue; 

    
      std::ostringstream regname;
      regname << "r" << i;
      out << regname.str() << "=" << cur << ";";

    }

#ifdef CONSTDOM_DEBUG
  std::cerr << " = " << out.str() << std::endl;
  std::cerr << std::endl;
#endif

  ConstDom* toret = new ConstDom(out.str());

  //copy current stack
  toret->stack = std::vector<std::string>(stack);
  toret->stackIsNegative = stackIsNegative;
  // If stack is top, it is contagious :-)
  if (stackIsTop || rhs->stackIsTop) {
    toret->stackIsTop = true;
  }

  //No effect on stack
  if (rhs->stack.size() == 0) {
  }
  //rhs has push effect on stack
  else if (rhs->stack.size() > 0 && !rhs->stackIsNegative) {
    // Extend the expressions on the stack
    for (std::vector<std::string>::iterator it = rhs->stack.begin(); it != rhs->stack.end(); it++) {
      cur = std::string(*it);
      cur = extendSingle(cur, vals);

      toret->stack.push_back(cur);
    }
  }
  //rhs has pop effect on stack
  else if (rhs->stack.size() > 0 && rhs->stackIsNegative) {
    if (stackIsNegative) { //already pop-effect, just append
      for (std::vector<std::string>::iterator it = rhs->stack.begin(); it != rhs->stack.end(); it++) {
        cur = std::string(*it);
        toret->stack.push_back(cur);
      }
    }
    else { //push \extend pop, need to resolve
      for (std::vector<std::string>::iterator it = rhs->stack.begin(); it != rhs->stack.end(); it++) {
        if (toret->stack.empty() || toret->stackIsNegative) {
          //XXX
          assert(false);
        }
        else {
          int regtopop = 0;
          if (!string_to_num<int>(regtopop, it->substr(1), std::dec))
            assert(false);
          std::string val = std::string(toret->stack.back());

#ifdef CONSTDOM_DEBUG
          std::cerr << "popping '" << val << "' into r" << regtopop << ", deciphered from " << *it << std::endl;
#endif

          toret->vals[regtopop] = val;
          toret->stack.pop_back();
        }
      }
    }
  }
  else {
    toret->stackIsTop = true;
  }

  return toret;
}

sem_elem_t ConstDom::combine( SemElem* se )
{
  ConstDom* rhs = static_cast< ConstDom* >(se);
  std::ostringstream out;
  std::string cur;

#ifdef CONSTDOM_DEBUG
  std::cerr << "Combine called for ";
  print(std::cerr);
  std::cerr << " ";
  rhs->print(std::cerr);
#endif

  // zero is neutral for combine
  if (isZero) {
    sem_elem_t a = new ConstDom(*rhs);

#ifdef CONSTDOM_DEBUG
    std::cerr << " = ";
    a->print(std::cerr);
    std::cerr << std::endl;
#endif

    return a;
  }
  else if (rhs->isZero) {
    sem_elem_t a = new ConstDom(*this);

#ifdef CONSTDOM_DEBUG
    std::cerr << " = ";
    a->print(std::cerr);
    std::cerr << std::endl;
#endif

    return a;
  }

  // combine each register's expression
  for (int i = 0; i < CONSTDOM_NUM_REGS; i++) {
    if (!rhs->vals[i].empty() && !vals[i].empty()) {
      if (rhs->vals[i] == vals[i])
        cur = vals[i];
      else
        cur = "top";
    }
    else if (rhs->vals[i].empty() && vals[i].empty()) {
      cur = "";
    }
    else {
      cur = "top";
    }

    std::ostringstream regname;
    regname << "r" << i;
    out << regname.str() << "=" << cur << ";";
  }

#ifdef CONSTDOM_DEBUG
  std::cerr << " = " << out.str() << std::endl;
  std::cerr << std::endl;
#endif

  ConstDom* toret = new ConstDom(out.str());

  //copy current stack
  toret->stack = std::vector<std::string>(stack);
  toret->stackIsNegative = stackIsNegative;
  // If stack is top, it is contagious :-)
  if (stackIsTop || rhs->stackIsTop) {
    toret->stackIsTop = true;
  }
  //TODO - combine the stacks

  return toret;
}

bool ConstDom::equal( SemElem* se ) const
{
  ConstDom* rhs = static_cast< ConstDom* >(se);

  if (isZero == true || rhs->isZero)
    return (isZero == rhs->isZero);
  
  if (stack.size() != rhs->stack.size())
    return false;

  for (int i = 0; i < CONSTDOM_NUM_REGS; i++) {
    if (vals[i] != rhs->vals[i])
      return false;
  }

  for (unsigned int i = 0; i < stack.size(); i++) {
    if (stack[i] != rhs->stack[i])
      return false;
  }

  return true;
}

std::ostream & ConstDom::print( std::ostream & o ) const
{
  o << "{ ";

  if (isZero) {
    o << "ZERO ";
  }
  else {
    for (int i = 0; i < CONSTDOM_NUM_REGS; i++) {
      if (!vals[i].empty())
        o << "r" << i << " = " << vals[i] << " ; ";
    }
  }
  o << "}";
  if (stackIsTop) {
    o << " top";
  }
  else if (!stack.empty()) {
    o << " [";
    if (!stackIsNegative)
      o << "push ";
    else
      o << "pop ";

    for (
        std::vector<std::string>::const_iterator it = stack.begin(); 
        it != stack.end(); 
        ++it) {
        o << *it << " ; ";
    }
    o << "]";
  }
  return o;
}

sem_elem_t ConstDom::from_string( const std::string& s ) const {
  //TODO
}


std::vector< std::string > ConstDom::asList() {
    std::vector< std::string > toRet;

    int i;
    for( i = 0; i < CONSTDOM_NUM_REGS; i++ ) {
      toRet.push_back( vals[i] );
    }

    return toRet;
}

std::vector< std::string > ConstDom::getStack() {
    std::vector< std::string > toRet = std::vector<std::string>(stack);

    return toRet;
}
