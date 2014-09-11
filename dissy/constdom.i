%module(directors="1") constdom


%include "/home/mchro/projects/WALi-3.4/Bindings/wali-common.i"

%{
/* Include implementation inline */
#include "ConstDom.cpp"

using namespace wali;
%}

%template(StringVector) std::vector<std::string>;
%template(ConstDomPtr) wali::ref_ptr<ConstDom>;
%include "ConstDom.hpp"

/* Methods for casting SemElem to ConstDom */
%inline %{
ConstDom* toConstDom(SemElem* w) {
        return dynamic_cast<ConstDom*>(w);
}

wali::ref_ptr<ConstDom> toConstDom(sem_elem_t w) {
        return wali::ref_ptr<ConstDom>( dynamic_cast<ConstDom*>(&(*w)) );
}
%}
