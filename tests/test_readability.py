import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def load_assets_module():
    spec = importlib.util.spec_from_file_location("readability_assets", ROOT / "readability_assets.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_simulator_module():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("simulate_refind", ROOT / "simulate_refind.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class KernelIconTests(unittest.TestCase):
    def test_make_kernel_icon_adds_accent_label_band_without_changing_top(self):
        assets = load_assets_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            base = tmp / "base.png"
            output = tmp / "icon.png"
            Image.new("RGBA", (128, 128), (10, 20, 30, 255)).save(base)

            assets.make_kernel_icon(base, "LTS", (120, 80, 200), output)

            with Image.open(output) as result:
                self.assertEqual(result.size, (128, 128))
                self.assertEqual(result.getpixel((0, 0)), (10, 20, 30, 255))
                accent_count = sum(
                    1
                    for y in range(102, 128)
                    for x in range(128)
                    if result.getpixel((x, y))[:3] == (120, 80, 200)
                )
                self.assertGreaterEqual(accent_count, 10)

    def test_create_kernel_icons_returns_three_kernel_specific_files(self):
        assets = load_assets_module()
        with tempfile.TemporaryDirectory() as tmp:
            outputs = assets.create_kernel_icons(Path(tmp))

            self.assertEqual(
                {path.name for path in outputs.values()},
                {"vmlinuz-linux.png", "vmlinuz-linux-lts.png", "vmlinuz-linux-pf.png"},
            )
            for path in outputs.values():
                self.assertTrue(path.is_file(), path)
                with Image.open(path) as image:
                    self.assertEqual(image.size, (128, 128))


class BackgroundEffectTests(unittest.TestCase):
    def test_panel_box_stays_left_of_character_face_region(self):
        assets = load_assets_module()
        self.assertLess(assets.PANEL_BOX[2], 2560 * 0.68)

    def test_frosted_panel_strength_and_a3_label_band(self):
        assets = load_assets_module()
        source = Image.new("RGBA", (2560, 1440), (180, 40, 60, 255))

        a1 = assets.apply_background_effects(source, "a1")
        a2 = assets.apply_background_effects(source, "a2")
        a3 = assets.apply_background_effects(source, "a3")

        self.assertNotEqual(a1.getpixel((1280, 700)), source.getpixel((1280, 700)))
        self.assertGreater(a2.getpixel((1280, 700))[0], a1.getpixel((1280, 700))[0])
        self.assertEqual(a3.getpixel((1280, 700)), source.getpixel((1280, 700)))
        self.assertNotEqual(a3.getpixel((1280, 920)), source.getpixel((1280, 920)))

    def test_a3_blurs_more_than_a1(self):
        assets = load_assets_module()
        source = Image.new("RGBA", (2560, 1440), (0, 0, 0, 255))
        source.putpixel((100, 100), (255, 255, 255, 255))

        a1 = assets.apply_background_effects(source, "a1")
        a3 = assets.apply_background_effects(source, "a3")

        self.assertLess(a3.getpixel((100, 100))[0], a1.getpixel((100, 100))[0])


class SimulatorIntegrationTests(unittest.TestCase):
    def test_original_variant_matches_existing_render_pixel_for_pixel(self):
        simulator = load_simulator_module()
        from PIL import ImageChops

        rendered = simulator.render_menu(
            Path("/boot/EFI/refind/themes/MomoneChinoi-hires/background.png"),
            variant="original",
        )
        with Image.open(ROOT / "renders/background.png") as expected:
            self.assertIsNone(ImageChops.difference(rendered, expected.convert("RGB")).getbbox())

    def test_a1_changes_kernel_icons_and_selected_label(self):
        simulator = load_simulator_module()
        with tempfile.TemporaryDirectory() as tmp:
            rendered = simulator.render_menu(
                ROOT / "candidates/yt_CPc5SuuOB6k.jpg",
                variant="a1",
                assets_dir=Path(tmp),
            )
        with Image.open(ROOT / "renders/yt_CPc5SuuOB6k.png") as original:
            original = original.convert("RGB")
            self.assertNotEqual(
                rendered.crop((980, 648, 1580, 792)).tobytes(),
                original.crop((980, 648, 1580, 792)).tobytes(),
            )
            self.assertNotEqual(
                rendered.crop((840, 896, 1720, 944)).tobytes(),
                original.crop((840, 896, 1720, 944)).tobytes(),
            )

    def test_long_selected_label_is_shrunk_to_fit_panel(self):
        simulator = load_simulator_module()
        font = simulator.label_font_for_width("X" * 60, 880)
        from PIL import ImageDraw

        width = ImageDraw.Draw(Image.new("RGB", (2560, 1440))).textlength("X" * 60, font=font)
        self.assertLessEqual(width, 880)
        self.assertGreaterEqual(font.size, 18)

    def test_improved_theme_conf_enables_labels_and_readable_paths(self):
        lines = (ROOT / "improved/theme.conf").read_text().splitlines()
        active = [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]
        self.assertNotIn("hideui label", active)
        self.assertIn("banner themes/MomoneChinoi-readable/background.png", active)
        self.assertIn("icons_dir themes/MomoneChinoi-readable/icons", active)

    def test_improved_install_staging_is_complete(self):
        with Image.open(ROOT / "improved/background.png") as background:
            self.assertEqual(background.size, (2560, 1440))
        for name in ("vmlinuz-linux.png", "vmlinuz-linux-lts.png", "vmlinuz-linux-pf.png"):
            self.assertTrue((ROOT / "improved/esp-root" / name).is_file(), name)
            self.assertTrue((ROOT / "improved/icons" / name).is_file(), name)
        for name in ("os_windows.png", "func_shutdown.png", "func_reset.png", "func_firmware.png", "func_exit.png"):
            self.assertTrue((ROOT / "improved/icons" / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
