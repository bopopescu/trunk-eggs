from App.ImageFile import ImageFile

from constants import *
import NyForum
import NyForumTopic
import NyForumMessage

from Products.Naaya import register_content
# Register as a folder content type
register_content(
    module=NyForum,
    klass=NyForum.NyForum,
    module_methods={'addNyForum': PERMISSION_ADD_FORUM},
    klass_methods={'forum_add_html': PERMISSION_ADD_FORUM},
    add_method=('forum_add_html', PERMISSION_ADD_FORUM),
)

def initialize(context):
    """ """

    #register classes
    context.registerClass(
        NyForum.NyForum,
        permission = PERMISSION_ADD_FORUM,
        constructors = (
                NyForum.manage_addNyForum_html,
                NyForum.addNyForum,
                ),
        icon = 'www/NyForum.gif'
        )

    context.registerClass(
        NyForumTopic.NyForumTopic,
        permission = PERMISSION_MODIFY_FORUMTOPIC,
        constructors = (
                NyForumTopic.manage_addNyForumTopic_html,
                NyForumTopic.addNyForumTopic,
                ),
        icon = 'www/NyForumTopic.gif'
        )

    context.registerClass(
        NyForumMessage.NyForumMessage,
        permission = PERMISSION_ADD_FORUMMESSAGE,
        constructors = (
                NyForumMessage.manage_addNyForumMessage_html,
                NyForumMessage.addNyForumMessage,
                ),
        icon = 'www/NyForumMessage.gif'
        )

    register_permissions()

misc_ = {
    'NyForum.gif':ImageFile('www/NyForum.gif', globals()),
    'NyForumTopic.gif':ImageFile('www/NyForumTopic.gif', globals()),
    'NyForumMessage.gif':ImageFile('www/NyForumMessage.gif', globals()),
    'attachment.gif':ImageFile('www/attachment.gif', globals()),
}

def register_permissions():
    from Products.Naaya.NySite import register_naaya_permission
    register_naaya_permission(PERMISSION_ADD_FORUM,
                              'Submit Forum objects')
    register_naaya_permission(PERMISSION_MODIFY_FORUMTOPIC,
                              'Forum - add / edit / modify topics')
    register_naaya_permission(PERMISSION_ADD_FORUMMESSAGE,
                              'Forum - submit messages')
    register_naaya_permission(PERMISSION_MODIFY_FORUMMESSAGE,
                              'Forum - edit messages')
