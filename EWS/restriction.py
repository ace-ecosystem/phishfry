from lxml import etree
from .namespaces import ENS, MNS, SNS, TNS, NSMAP

def Restriction(field, value):
        restriction = etree.Element("{%s}Restriction" % MNS)
        equal_to = etree.SubElement(restriction, "{%s}IsEqualTo" % TNS)
        field_uri = etree.SubElement(equal_to, "{%s}FieldURI" % TNS, FieldURI=field)
        field_uri_value = etree.SubElement(equal_to, "{%s}FieldURIOrConstant" % TNS)
        etree.SubElement(field_uri_value, "{%s}Constant" % TNS, Value=value)
        return restriction
