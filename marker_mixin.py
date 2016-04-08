class MarkerMixin(object):
    def __init__(self, *args, **kwargs):
        super(MarkerMixin, self).__init__(*args, **kwargs)

        self._markers = []

    @property
    def markers(self):
        return self._markers

    @markers.setter
    def markers(self, value):
        for marker in self._markers:
            marker.changed.disconnect(self._markers_changed)

        self._markers = value

        for marker in self._markers:
            marker.changed.connect(self._markers_changed)

    def _markers_changed(self):
        raise NotImplementedError("You have to impement this in your subclass")