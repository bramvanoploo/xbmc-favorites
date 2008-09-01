# vim: fileencoding=utf8
from cStringIO import StringIO
#import xml.dom.minidom
from xml.dom.minidom import parseString
import logging
import codecs
import datetime
import time
import struct
import urllib2
import amf, amf0

RESPONSE_RESULT = '/onResult'
RESPONSE_STATUS = '/onStatus'
# RESPONSE_DEBUG_EVENTS = '/onDebugEvents'

#logger = logging.getLogger('AMF')
#logger.setLevel(logging.INFO)
#handler = logging.StreamHandler()
#logger.addHandler(handler)
 
#def set_logger(l):
#    global logger
#    logger = l

class AMFMessageBody(object):

    def __init__(self, target, response, data):
        self.target = target
        self.response = response
        self.data = data
        self.__service_name = None
        self.__service_method_name = None

    def __get_service_method_path(self):
        if not self.__service_name or not self.__service_method_name:
            self.__setup_target()
        return self.__service_name + '/' + self.__service_method_name
    service_method_path = property(__get_service_method_path)

    def __setup_target(self):
        dotIndex = self.target.rfind('.')
        if dotIndex > 0:
            self.__service_name = self.target[:dotIndex]
            self.__service_method_name = self.target[dotIndex+1:]

    def __get_args(self):
        if isinstance(self.data, (tuple, list)):
            return self.data
        return []
    args = property(__get_args)

    def _get_cache_key(self):
        self.target + str(self.data)
         
    def __str__(self):
        return "target=%s,response=%s,data=%s" % (self.target, self.response, self.data)


class AMFMessage(object):

    def __init__(self):
        self.headers = []
        self.headerMap = {}
        self.bodies = []
        self.version = 3
        self.use_cache = False

    def add_header(self, amfHeader):
        self.headers.append(amfHeader)
        self.headerMap[amfHeader['name']] = amfHeader['value']
        if amfHeader['name'].lower() == 'use-cache':
            self._set_cache(amfHeader)

    def get_header(self, name):
        return self.headerMap.get(name, None)

    def _set_cache(self, amfHeader):
        if int(amfHeader['value']) > 0:
            self.use_cache = True
            self.cache_timeout = int(amfHeader['value'])
        else:
            self.use_cache = False
            self.cache_timeout = 0

    def add_body(self, amfBody):
        self.bodies.append(amfBody)

    def get_body_count(self):
        return len(self.bodies)

    def __str__(self):
        return "AMFMessage object [%d headers, %d bodies]" % (len(self.headers), len(self.bodies))


class AMFMessageBodyContext(object):

    def __init__(self):
        self._str_refs = []
        self._obj_refs = []
        self._class_def_refs = []
#
    def add_string_reference(self, str):
        #amf.logger.debug("add_string_reference(%s) -- index='%d'", repr(str), len(self._str_refs))
        self._str_refs.append(str)

    def get_string_reference(self, index):
        str = self._str_refs[index]
        #amf.logger.debug("get_string_reference(%d) -- %s", index, repr(str))
        return str

    def get_string_reference_index(self, str):
        try:
            return self._str_refs.index(str)
        except ValueError:
            return -1

    def add_object_reference(self, obj):
        #amf.logger.debug("add_object_reference(%s) -- index='%d'", repr(obj), len(self._obj_refs))
        self._obj_refs.append(obj)

    def get_object_reference(self, index):
        obj = self._obj_refs[index]
        #amf.logger.debug("get_object_reference(%d) -- %s", index, repr(obj))
        return obj

    def get_object_reference_index(self, obj):
        try:
            return self._obj_refs.index(obj)
        except ValueError:
            return -1

    def add_class_def_reference(self, class_def):
        #amf.logger.debug("add_class_def_reference(%s) -- index='%d'", repr(class_def), len(self._class_def_refs))
        self._class_def_refs.append(class_def)

    def get_class_def_reference(self, index):
        class_def = self._class_def_refs[index]
        #amf.logger.debug("get_class_def_reference(%d) -- %s", index, repr(class_def))
        return class_def

    def get_class_def_reference_index(self, class_def):
        try:
            return self._class_def_refs.index(class_def)
        except ValueError:
            return -1


class ByteArray(object):

    def __init__(self, data):
        self.data = data


class AMFAuthenticationError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def read(raw_post_data):
    """
    Parse the given data and return the AMFMessage object.
    """
    # for debug
    #__write_data_to_file(raw_post_data)
    return amf0.read(raw_post_data)

def __write_data_to_file(data):
    """
    Write the given data to '/tmp/postdata.dat'.
    This function is for debugging.
    """
    import os, os.path
    dir = os.environ['TMP']
    file = os.path.join(dir, 'postdata.dat')
    f = open(file, 'wb')
    f.write(data)
    f.close()

def write(message):
    """
    Convert the given AMFMessage object to binary data, and return it.
    """
    amf_version = message.version
    if amf_version == 3:
        import amf3
        return amf3.write(message)
    else:
        return amf0.write(message)


class RPCServiceInvocationError(Exception):

    def __init__(self, result, faultString='', faultDetail='', faultCode=''):
        self.result = result
        self.faultString = faultString
        self.faultDetail = faultDetail
        self.faultCode = faultCode

    def __str__(self):
        return repr(self.faultString)


class RPCMethodCall(object):

    def __init__(self, gatewayUrl, serviceName, methodName, version=3, requestCount=1, username=None, password=None):
        self.gatewayUrl = gatewayUrl
        self.serviceName = serviceName
        self.methodName = methodName
        self.version = version
        self.requestCount = requestCount
        self.username = username
        self.password = password

    def __build_amf_message(self, args):
        message = AMFMessage()
        message.version = self.version
        # header 
        if self.username and self.password:
            self.__set_credentials(message)
        # body
        target = self.serviceName + '.' + self.methodName
        response = '/' + str(self.requestCount)
        body = AMFMessageBody(target, response, args)
        message.add_body(body)
        return message

    def __set_credentials(self, message):
        if message.version == 3:
            usernameHeader = {'name' : 'credentialsUsername', 'value' : self.username}
            passwordHeader = {'name' : 'credentialsPassword', 'value' : self.password}
            message.add_header(usernameHeader)
            message.add_header(passwordHeader)
        else:
            header = {'name' : 'Credentials', 'value' : {'userid' : self.username, 'password' : self.password}}
            message.add_header(header)

    def __call__(self, *args):
        requestMessage = self.__build_amf_message(args)
        postdata = write(requestMessage)
        req = urllib2.Request(url=self.gatewayUrl, data=postdata)
        req.add_header('Content-type', 'application/x-amf')
        #req.add_header('Referer', 'http://hetgesprek.fabflows.com/media/player/gesprek.swf?p=g56bfa807e6405552278376d8479a1525')
        f = urllib2.urlopen(req)
        raw_data = f.read()
        f.close()
        responseMessage = read(raw_data)
        result = responseMessage.bodies[0].data # The response message has only one message body in this case.
        if responseMessage.bodies[0].target.endswith(RESPONSE_STATUS):
            # False. Convert the response AMFMessage into an exception and throw it.
            raise RPCServiceInvocationError(
                    result=result,
                    faultString=result.get('description', ''),
                    faultDetail=result.get('details', ''),
                    faultCode=result.get('code', '')
                    )
        else:
            return result
        

class RemotingService(object):

    def __init__(self, gatewayUrl, serviceName, version=3):
        self._serviceName = serviceName
        self._gatewayUrl = gatewayUrl
        if not version == 3 and not version == 0:
            raise ValueError, 'Version must be 0 or 3.'
        self.__version__ = version
        self._username = None
        self._password = None
        self._requestCount = 0

    def __repr__(self):
        return 'amf.RemotingService(%r, %r, %r)' % (self._gatewayUrl, self._serviceName, self.__version__)

    def setCredentials(self, username, password):
        self._username = username
        self._password = password

    def __getattr__(self, name):
        self._requestCount += 1
        return RPCMethodCall(gatewayUrl=self._gatewayUrl,
                serviceName=self._serviceName,
                methodName=name,
                version=self.__version__,
                requestCount=self._requestCount,
                username=self._username,
                password=self._password)

