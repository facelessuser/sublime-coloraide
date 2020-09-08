"""Color tools."""
from .. import util
from ..util import convert

WHITE = [1.0] * 3
BLACK = [0.0] * 3


def calc_contrast_ratio(lum1, lum2):
    """Get contrast ratio."""

    return (lum1 + 0.05) / (lum2 + 0.05) if (lum1 > lum2) else (lum2 + 0.05) / (lum1 + 0.05)


def calc_luminance(srgb):
    """Calculate luminance from `srgb` coordinates."""

    lsrgb = convert.lin_srgb(srgb)
    vector = [0.2126, 0.7152, 0.0722]
    return sum([r * v for r, v in zip(lsrgb, vector)])


class _ColorTools:
    """Color utilities."""

    def _mix_channel(self, c1, c2, f1, f2=1.0):
        """
        Blend the channel.

        `f1` is the blend percent.
        When simulating transparency, `f1` can be looked at as the foreground alpha,
        while `f2` would be the background `alpha`. Usually we `f2` is always `1.0`
        as we normally overlay a transparent color on an opaque one.
        """

        return abs(c1 * f1 + c2 * f2 * (1 - f1))

    def _hue_mix_channel(self, c1, c2, f1, f2=1.0, scale=360.0):
        """Blend the hue style channel."""

        c1 *= scale
        c2 *= scale

        if abs(c1 % 360 - c2) > 180.0:
            if c1 < c2:
                c1 += 360.0
            else:
                c2 += 360.0

        value = self._mix_channel(c1, c2, f1, f2)
        if not (0.0 <= value <= 360.0):
            value = value % 360.0

        return value / scale

    def luminance(self):
        """Get perceived luminance."""

        return calc_luminance(convert.convert(self.coords(), self.space(), "srgb"))

    def min_contrast(self, color, target):
        """
        Get the color with the best contrast.

        # https://drafts.csswg.org/css-color/#contrast-adjuster
        """

        lum1 = self.luminance()
        lum2 = color.luminance()
        ratio = calc_contrast_ratio(lum1, lum2)

        if target <= 0:
            self.mutate(color)
            return

        required_lum = ((lum2 + 0.05) / target) - 0.05
        if required_lum < 0:
            required_lum = target * (lum2 + 0.05) - 0.05

        if ratio < target:
            mix = self.new(WHITE if lum2 < lum1 else BLACK, "srgb")
        else:
            mix = color.convert("srgb")

        min_mix = 0.0
        max_mix = 1.0

        temp = self.clone().convert("srgb")
        r, g, b = temp._cr, temp._cg, temp._cb

        last_lum = util.INF
        last_mix = 0

        while abs(min_mix - max_mix) > 0.001:
            mid_mix = (max_mix + min_mix) / 2

            temp._mix([r, g, b], mix.coords(), mid_mix)

            lum2 = temp.luminance()

            if lum2 > required_lum:
                min_mix = mid_mix
            else:
                max_mix = mid_mix

            if lum2 >= required_lum and lum2 < last_lum:
                last_lum = lum2
                last_mix = mid_mix

        # Use the best, last values
        temp._mix([r, g, b], mix.coords(), last_mix)
        self.mutate(temp)

    def contrast_ratio(self, color):
        """Get contrast ratio."""

        return calc_contrast_ratio(self.luminance(), color.luminance())

    def is_dark(self):
        """Check if color is dark."""

        return self.luminance() < 0.5

    def is_light(self):
        """Check if color is light."""

        return self.luminance() >= 0.5

    def alpha_composite(self, background=None):
        """
        Apply the given transparency with the given background.

        This gives a color that represents what the eye sees with
        the transparent color against the given background.
        """

        if background is None:
            background = self.new(self.DEF_BG)
        elif not isinstance(background, type(self)):
            background = self.new(background)

        if self._alpha < 1.0:
            # Blend the channels using the alpha channel values as the factors
            # Afterwards, blend the alpha channels. This is different than blend.
            self._mix(background, self._alpha, background._alpha)
            self._alpha = self._alpha + background._alpha * (1.0 - self._alpha)
        return self

    def mix(self, color, percent, alpha=False, space="lch"):
        """Blend color."""

        space = space.lower()
        factor = util.clamp(float(percent), 0.0, 1.0)

        this = None
        if self.space() == space:
            this = self
        else:
            this = self.convert(space)

        if color.space() != space:
            color = color.convert(space)

        if this is None:
            raise ValueError('Invalid colorspace value: {}'.format(space))

        this._mix(this.coords(), color.coords(), factor)
        if alpha:
            # This is a simple channel blend and not alpha compositing.
            this._alpha = self._mix_channel(this._alpha, color._alpha, factor)

        self.mutate(this)

    def invert(self):
        """Invert the color."""

        this = self.convert("srgb") if self.space() != "srgb" else self
        this._cr ^= 0xFF
        this._cg ^= 0xFF
        this._cb ^= 0xFF
        self.mutate(this)

    def grayscale(self):
        """Convert the color with a grayscale filter."""

        self._grayscale()
