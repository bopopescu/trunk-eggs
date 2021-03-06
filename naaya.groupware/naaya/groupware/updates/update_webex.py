from Products.naayaUpdater.updates import UpdateScript
from Products.NaayaBase.constants import PERMISSION_REQUEST_WEBEX
from AccessControl.Permission import Permission


class UpdateWebEx(UpdateScript):
    """ """
    title = ('Add WebEx planing email link, '
             'remove it if it appears more than once')
    creation_date = 'Jun 30, 2014'
    authors = ['Valentin Dumitru']
    description = ('Add WebEx planing email link, '
                   'remove possible duplicated links to the WebEx feature '
                   'introduced by a faulty update script.')

    def _update(self, portal):
        portlets_tool = portal.getPortletsTool()
        menunav_links = portlets_tool['menunav_links']
        link_ids = []
        for link_id, link in menunav_links.get_links_collection().items():
            if link.title == 'WebEx planning mail':
                link_ids.append(link_id)
        if len(link_ids) == 0:
            menunav_links.manage_add_link_item(
                id='webex', title='WebEx planning mail', description='',
                url='/admin_webex_mail_html', relative='1',
                permission='Naaya - Publish content', order='55')
            self.log.debug('Link added to the Navigation portlet')
        elif len(link_ids) == 1:
            self.log.debug('No duplicated links found')
        elif len(link_ids) > 1:
            menunav_links.manage_delete_links(ids=link_ids[1:])
            self.log.debug('%s links deleted from the Navigation portlet' %
                           len(link_ids[1:]))
        return True


class UpdateWebExLink(UpdateScript):
    """ """
    title = 'Display the link to WebEx planing for Contributors'
    creation_date = 'Mar 3, 2014'
    authors = ['Valentin Dumitru']
    description = ('Display the link to WebEx planing for Contributor')

    def _update(self, portal):
        portlets_tool = portal.getPortletsTool()
        menunav_links = portlets_tool['menunav_links']
        for link_id, link in menunav_links.get_links_collection().items():
            if link.title == 'WebEx planning mail':
                if link.permission == 'Naaya - Skip approval':
                    self.log.debug('Permission already updated')
                else:
                    item = link.id
                    portal.admin_editlink(id='menunav_links',
                                          item=item,
                                          title='WebEx planning mail',
                                          description='',
                                          url='/admin_webex_mail_html',
                                          relative='1',
                                          permission='Naaya - Skip approval',
                                          order='55')
                break
        else:
            self.log.error('Link with title "WebEx planning mail" not found '
                           'in menunav_links, run "Add WebEx planing..." '
                           'update first')
        return True


class UpdateWebExPermission(UpdateScript):
    """ """
    title = 'Add Contributors to the WebEx permission'
    creation_date = 'Mar 10, 2014'
    authors = ['Valentin Dumitru']
    description = ('Add Contributors to the WebEx permission')

    def _update(self, portal):
        webex_perm = Permission(PERMISSION_REQUEST_WEBEX, (), portal)
        roles_with_webex = webex_perm.getRoles()
        if isinstance(roles_with_webex, list):
            acquire = 1
        else:
            acquire = 0
        if 'Contributor' not in roles_with_webex:
            roles = set(roles_with_webex)
            roles.update(['Administrator', 'Manager', 'Contributor'])
            portal.manage_permission(PERMISSION_REQUEST_WEBEX,
                                     list(roles), acquire=acquire)
            self.log.debug(
                'Contributor added to the "Request WebEx permission"')
        else:
            self.log.debug('Contributor already has the permission')
        return True
