#ifndef CONSTDOM_GUARD
#define CONSTDOM_GUARD 1

/*!
 * @author Mads Chr. Olesen
 */

#include <wali/SemElem.hpp>
#define CONSTDOM_NUM_REGS 16

using wali::SemElem;
using wali::sem_elem_t;

class ConstDom : public wali::SemElem
{

  public:

    ConstDom( );
    ConstDom( std::string val, std::string stackeffect="" );

    virtual ~ConstDom();

    sem_elem_t one() const;

    sem_elem_t zero() const;

    // zero is the annihilator for extend
    sem_elem_t extend( SemElem* rhs );

    // zero is neutral for combine
    sem_elem_t combine( SemElem* rhs );

    bool equal( SemElem* rhs ) const;

    std::ostream & print( std::ostream & o ) const;

    sem_elem_t from_string( const std::string& s ) const;

    std::vector< std::string > asList();

    std::vector< std::string > getStack();

  protected:
    std::string vals[CONSTDOM_NUM_REGS];
    std::vector<std::string> stack;
    bool stackIsNegative;

    bool stackIsTop;
    bool isZero;

    void tokenize(const std::string& str,
                      std::vector<std::string>& tokens,
                      const std::string& delimiters = " ");

};

#endif	// CONSTDOM_GUARD

