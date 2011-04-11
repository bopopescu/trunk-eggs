"""
This module contains the class that implements the Naaya file system
folder type of object. All types of objects that are file system containers
must extend this class.
"""
import zLOG
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from Products.NaayaBase.NyContainer import NyContainer

EXTFILE_INSTALLED = True
try:
    from Products.ExtFile.ExtFile import manage_addExtFile
except ImportError:
    zLOG.LOG("NyFSContainer", zLOG.WARNING,
             "ExtFile is not installed => all files will be stored in ZODB")
    EXTFILE_INSTALLED = False

class NyFSContainer(NyContainer):
    """ Class that implements the Naaya file system folder type of object.
    """
    is_ext = EXTFILE_INSTALLED
    def __init__(self):
        NyContainer.__init__(self)

    def manage_addFile(self, id, file="", **kwargs):
        if self.is_ext:
            return manage_addExtFile(self, id=id, file=file)
        return NyContainer.manage_addFile(self, id, file)

    def update_data(self, data, content_type=None, size=None, filename=''):
        self.manage_delObjects(self.objectIds())
        filename = filename or 'attached-file'
        id = self.utSlugify(filename)
        child_id = self.manage_addFile(id)
        child = self._getOb(child_id)
        if getattr(data, 'index_html', None):
            data = data.index_html()
        child.manage_upload(data, content_type)

    def isReady(self, fid):
        """ Check if file exists
        """
        doc = self._getOb(fid)
        if not self.is_ext:
            return doc and True or False
        return not doc.is_broken()

    def _get_attached_file(self, sid=None):
        # Returns object in container by sid.
        # If sid not provided return first subobject
        if not sid:
            attached_files = self.objectValues(["ExtFile", "File"])
            if not attached_files:
                return None
            return attached_files[0]
        return getattr(self, sid, None)

    def get_size(self, sid=None):
        # Return size of file with provided id. If no id provided,
        # returns size of the first object in container.
        attached_file = self._get_attached_file(sid)
        if not attached_file:
            return 0
        return attached_file.get_size()

    # XXX Backward compatible
    def getSize(self, sid=None):
        # Use get_size instead
        return self.get_size(sid)

    def get_data(self, sid=None, as_string=True):
        # Child data view.
        attached_file = self._get_attached_file(sid)
        if as_string:
            if not attached_file:
                return ''
            return attached_file.index_html()
        return attached_file

    def _get_data_name(self, sid=None):
        # Child disk path
        data = self.get_data(sid=sid, as_string=False)
        return getattr(data, 'filename', [])

    def index_html(self, REQUEST=None, RESPONSE=None):
        # Child view
        sid = None
        if REQUEST:
            sid = REQUEST.form.get('sid', None)
        return self.get_data(sid)

    def getContentType(self, sid=None):
        # Child content-type
        attached_file = self._get_attached_file(sid)
        if not attached_file:
            return ''
        return attached_file.getContentType()

InitializeClass(NyFSContainer)
