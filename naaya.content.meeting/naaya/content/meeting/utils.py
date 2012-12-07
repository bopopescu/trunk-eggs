# !!!! These should be moved to auth_tool

def _encode(val):
    if val is None:
        return ''
    if isinstance(val, unicode):
        return val.encode('utf-8')
    return unicode(val, 'iso-8859-1').encode('utf-8')

def schemaHasParam(acl_folder, param):
    for item in acl_folder.getLDAPSchema():
        if item[0] == param:
            return True
    return False

def getUserFullName(site, uid):
    auth_tool = site.getAuthenticationTool()
    local_user = auth_tool.getUser(uid)
    if local_user is not None:
        username = auth_tool.getUserFullName(local_user)
        return _encode(username)

    for source in auth_tool.getSources():
        acl_folder = source.getUserFolder()
        if schemaHasParam(acl_folder, 'cn'):
            user = acl_folder.getUserById(uid, None)
            if user is not None:
                return _encode(user.getProperty('cn'))

def getUserEmail(site, uid):
    auth_tool = site.getAuthenticationTool()
    local_user = auth_tool.getUser(uid)
    if local_user is not None:
        return auth_tool.getUserEmail(local_user)

    for source in auth_tool.getSources():
        acl_folder = source.getUserFolder()
        if schemaHasParam(acl_folder, 'mail'):
            user = acl_folder.getUserById(uid, None)
            if user is not None:
                return _encode(user.getProperty('mail'))

def getUserOrganization(site, uid):
    auth_tool = site.getAuthenticationTool()
    local_user = auth_tool.getUser(uid)
    if local_user is not None:
        return ''

    for source in auth_tool.getSources():
        acl_folder = source.getUserFolder()
        if schemaHasParam(acl_folder, 'o'):
            user = acl_folder.getUserById(uid, None)
            if user is not None:
                return _encode(user.getProperty('o'))

def getUserPhoneNumber(site, uid):
    auth_tool = site.getAuthenticationTool()
    local_user = auth_tool.getUser(uid)
    if local_user is not None:
        return ''

    for source in auth_tool.getSources():
        acl_folder = source.getUserFolder()
        if schemaHasParam(acl_folder, 'telephoneNumber'):
            user = acl_folder.getUserById(uid, None)
            if user is not None:
                return _encode(user.getProperty('telephoneNumber'))

def findUsers(site, search_param, search_term):
    def userMatched(uid, cn):
        if search_param == 'uid':
            return search_term in uid
        elif search_param == 'cn':
            return search_term.encode('utf-8') in cn
        else:
            return False

    auth_tool = site.getAuthenticationTool()
    ret = []

    for user in auth_tool.getUsers():
        uid = auth_tool.getUserAccount(user)
        cn = auth_tool.getUserFullName(user)
        info = 'Local user'

        if userMatched(uid, cn):
            ret.append({'uid': uid, 'cn': cn, 'organization': '', 'info': info})

    for source in auth_tool.getSources():
        acl_folder = source.getUserFolder()
        if schemaHasParam(acl_folder, search_param):
            users = acl_folder.findUser(search_param=search_param, search_term=search_term)
            for user in users:
                uid = user.get('uid', '')
                cn = _encode(user.get('cn', ''))
                mail = user.get('mail', '')
                organization = _encode(user.get('o', ''))
                info = user.get('dn', '')
                ret.append({
                    'uid': uid,
                    'cn': cn,
                    'mail': mail,
                    'organization': organization,
                    'info': info
                })

    return ret

def listUsersInGroup(site, search_role):
    auth_tool = site.getAuthenticationTool()
    ret = []

    for source in auth_tool.getSources():
        acl_folder = source.getUserFolder()
        users = source.getUsersByRole(acl_folder, [(search_role, None)])
        for user in users:
            ret.append({
                'uid': user.user_id,
                'cn': _encode(user.full_name),
                'organization': _encode(user.organisation),
                'info': user.dn,
            })

    return ret


