from Products.NaayaCore.FormsTool.NaayaTemplate import NaayaPageTemplateFile

_admin_assign_role = NaayaPageTemplateFile('zpt/site_admin_roles', globals(),
                      'site_admin_roles')

def admin_assign_role(context, REQUEST):
    orig_id = REQUEST.get('orig_id')
    object_paths = REQUEST.get('object_paths', [])
    new_users = REQUEST.get('new_users', [])
    messages = []
    options = {}
    users = context.getAuthenticationTool().getUsersWithRole('Contributor')
    user_ids = sorted(users.keys())
    if orig_id == '':
        messages.append('Please select a user to search for content.')
        orig_id = None
    options['users'] = users
    options['user_ids'] = user_ids
    if not orig_id:
        options['messages'] = messages
        return _admin_assign_role.__of__(context)(REQUEST, **options)
    if REQUEST.has_key('assign_role'):
        if isinstance(object_paths, basestring):
            object_paths = [object_paths]
        if isinstance(new_users, basestring):
            new_users = [new_users]
        if not object_paths:
            messages.append('Please select at least one object to assign role to.')
        else:
            options['object_paths'] = object_paths
        if not new_users:
            messages.append('Please select at least one user to assign role to.')
        else:
            options['new_users'] = new_users
        if object_paths and new_users:
            for path in object_paths:
                ob = context.getSite().restrictedTraverse(path)
                for user_id in new_users:
                    ob.manage_setLocalRoles(user_id, ['Editor'])
    obj_list = context.getCatalogedObjects(contributor=orig_id)
    if not obj_list:
        messages.append("User %s doesn't have contributions on this site yet." % orig_id)
    objects = {}
    for ob in obj_list:
        local_roles = ob.__ac_local_roles__ or {}
        objects ['/'.join(ob.getPhysicalPath())] = [ob.title_or_id(),
                                                    local_roles]
    options['messages'] = messages
    options['objects'] = objects
    return _admin_assign_role.__of__(context)(REQUEST, **options)

