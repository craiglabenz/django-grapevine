from __future__ import unicode_literals


def parse_email(address):
    """
    Returns "Marco Polo", "marco@polo.com" from "Marco Polo <marco@polo.com"
    Returns "", "marco@polo.com" from "marco@polo.com"
    """
    if ' ' in address.strip():
        assert '<' in address and '>' in address, "Invalid address structure: %s" % (address,)
        parts = address.split(' ')
        name = ' '.join(parts[:-1])
        address = parts[-1][1:-1]

        return name, address
    else:
        return "", address


class EventRepo(object):
    _instance = None
    name_map = {}

    def __new__(cls, *args, **kwargs):
        """
        Singleton implementation
        """
        if not cls._instance:
            cls._instance = super(EventRepo, cls).__new__(cls, *args, **kwargs)
            cls._instance.seed_name_map()
        return cls._instance

    def seed_name_map(self):
        from models import Event
        self.name_map = {}
        for ev in Event.objects.all():
            self._instance.name_map[ev.name] = ev

    def get_event_by_name(self, name):
        return self.name_map[name]

    def __getitem__(self, name):
        return self.get_event_by_name(name)
