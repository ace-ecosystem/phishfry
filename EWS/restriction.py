from lxml import etree
from .namespaces import ENS, MNS, SNS, TNS, NSMAP

def Restriction(expression):
        restriction = etree.Element("{%s}Restriction" % MNS)
        restriction.append(expression)
        return restriction

def And(expression_a, expression_b):
    expression = etree.Element("{%s}And" % TNS)
    expression.append(expression_a)
    expression.append(expression_b)
    return expression

def Or(expression_a, expression_b):
    expression = etree.Element("{%s}Or" % TNS)
    expression.append(expression_a)
    expression.append(expression_b)
    return expression

def IsEqualTo(field, value):
    expression = etree.Element("{%s}IsEqualTo" % TNS)
    field_uri = etree.SubElement(expression, "{%s}FieldURI" % TNS, FieldURI=field)
    field_uri_value = etree.SubElement(expression, "{%s}FieldURIOrConstant" % TNS)
    etree.SubElement(field_uri_value, "{%s}Constant" % TNS, Value=value)
    return expression

def Contains(field, value):
    expression = etree.Element("{%s}Contains" % TNS, ContainmentMod="Substring", ContainmentComparison="Exact")
    field_uri = etree.SubElement(expression, "{%s}FieldURI" % TNS, FieldURI=field)
    etree.SubElement(expression, "{%s}Constant" % TNS, Value=value)
    return expression
