"""LAB class."""
from .base import _Color
from .tools import _ColorTools
from .. import util
from ..util import parse
from ..util import convert


class _LAB(_ColorTools, _Color):
    """LAB class."""

    COLORSPACE = "lab"
    DEF_BG = "[0, 0, 0, 1]"

    def __init__(self, color=None):
        """Initialize."""

        super().__init__(color)

        if isinstance(color, _Color):
            self._cl, self._ca, self._cb = convert.convert(color.coords(), color.space(), self.space())
            self._alpha = color._alpha
        elif isinstance(color, str):
            values = self.match(color)[0]
            if values is None:
                raise ValueError("'{}' does not appear to be a valid color".format(color))
            self._cl, self._ca, self._cb, self._alpha = values
        elif isinstance(color, (list, tuple)):
            if not (3 <= len(color) <= 4):
                raise ValueError("A list of channel values should be of length 3 or 4.")
            self._cl = color[0]
            self._ca = color[1]
            self._cb = color[2]
            self._alpha = 1.0 if len(color) == 3 else color[3]
        else:
            raise TypeError("Unexpected type '{}' received".format(type(color)))

    @property
    def _cl(self):
        """Hue channel."""

        return self._c1

    @_cl.setter
    def _cl(self, value):
        """
        Set hue channel.

        Theoretically, there is no upper bound here. HDR may use much higher.

        TODO: Do we clamp the higher end or not?
        """

        self._c1 = util.clamp(value, 0.0, None)

    @property
    def _ca(self):
        """A on LAB axis."""

        return self._c2

    @_ca.setter
    def _ca(self, value):
        """
        Set A on LAB axis.

        Theoretically unbounded. It is mentioned in the
        specification that generally the range is +/- 160.

        TODO: Should we not clamp this?
        """

        self._c2 = util.clamp(value, None, None)

    @property
    def _cb(self):
        """B on LAB axis."""

        return self._c3

    @_cb.setter
    def _cb(self, value):
        """
        Set B on LAB axis.

        Theoretically unbounded.

        TODO: Should we not clamp this?
        """

        self._c3 = util.clamp(value, None, None)

    def __str__(self):
        """String."""

        return self.to_string(alpha=True)

    def _grayscale(self):
        """Convert to grayscale."""

        self._ca = 0
        self._cb = 0

    def _mix(self, coords1, coords2, factor, factor2=1.0):
        """Blend the color with the given color."""

        self._cl = self._mix_channel(coords1[0], coords2[0], factor, factor2)
        self._ca = self._mix_channel(coords1[1], coords2[1], factor, factor2)
        self._cb = self._mix_channel(coords1[2], coords2[2], factor, factor2)

    @property
    def l(self):
        """L channel."""

        return self._cl

    @l.setter
    def l(self, value):
        """Get true luminance."""

        self._cl = self.tx_channel(0, value) if isinstance(value, str) else float(value)

    @property
    def a(self):
        """A channel."""

        return self._ca

    @a.setter
    def a(self, value):
        """A axis."""

        self._ca = self.tx_channel(1, value) if isinstance(value, str) else float(value)

    @property
    def b(self):
        """B channel."""

        return self._cb

    @b.setter
    def b(self, value):
        """B axis."""

        self._cb = self.tx_channel(2, value) if isinstance(value, str) else float(value)

    @classmethod
    def tx_channel(cls, channel, value):
        """Translate channel string."""

        return float(value)

    @classmethod
    def split_channels(cls, color):
        """Split channels."""

        channels = []
        for i, c in enumerate(parse.RE_COMMA_SPLIT.split(color[1:-1].strip()), 0):
            if i <= 2:
                channels.append(cls.tx_channel(i, c))
            else:
                channels.append(cls.tx_channel(-1, c))
        if len(channels) == 3:
            channels.append(1.0)
        return channels
