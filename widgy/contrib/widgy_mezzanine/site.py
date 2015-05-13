from mezzanine.utils.sites import current_site_id, has_site_permission
from widgy.models import Content
from widgy.site import WidgySite

class WidgySiteMultiMixin(object):
    def has_add_permission(self, request, parent, new_object_class):
        codename = get_permission_codename('add', new_object_class._meta)
        if isinstance(parent, Content):
            a = any(current_site_id() == o.site_id for o in parent.get_root().node.versiontracker_set.get().owners)
            if not has_site_permission(request.user) or not a:
                return False
        return request.user.has_perm('%s.%s' % (new_object_class._meta.app_label, codename))


    def has_change_permission(self, request, obj_or_class):
        codename = get_permission_codename('change', obj_or_class._meta)
        if isinstance(obj_or_class, Content):
            a = any(current_site_id() == o.site_id for o in obj_or_class.get_root().node.versiontracker_set.get().owners)
            if not has_site_permission(request.user) or not a:
                return False
        return request.user.has_perm('%s.%s' % (obj_or_class._meta.app_label, codename))

    def has_delete_permission(self, request, obj_or_class):
        def has_perm(o):
            codename = get_permission_codename('delete', o._meta)
            if isinstance(obj_or_class, Content):
                a = any(current_site_id() == o.site_id for o in obj_or_class.get_root().node.versiontracker_set.get().owners)
                if not has_site_permission(request.user) or not a:
                    return False
            return request.user.has_perm('%s.%s' % (o._meta.app_label, codename))

        if isinstance(obj_or_class, type):
            return has_perm(obj_or_class)
        else:
            return all(map(has_perm, obj_or_class.depth_first_order()))

class WidgySiteMultiSite(WidgySiteMultiMixin, WidgySite):
    pass
