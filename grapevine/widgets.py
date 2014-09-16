# Django
from django.contrib.admin.widgets import ForeignKeyRawIdWidget


class GrapevineForeignKeyRawIdWidget(ForeignKeyRawIdWidget):
    def render(self, name, value, attrs=None):
        """
        Extends super.render by adding a Bootstrap class to the ForeignKeyRawId widget
        """
        if attrs is None:
            attrs = {}
        attrs.setdefault('class', '')
        attrs['class'] += ' form-control'

        # Now that we've added the class to attrs, call super.render
        return super(GrapevineForeignKeyRawIdWidget, self).render(name, value, attrs)
