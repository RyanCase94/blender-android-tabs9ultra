# Blender for Galaxy Tab S9 Ultra

Personal experimental Android build based on
[Simfeo Android Alpha 4](https://github.com/simfeo/blender/releases/tag/android-alpha-4),
source commit `d93bd33cba768e19ee4387a31c0ea137ee2f0047`.
This is a community build of Blender 5.3 alpha.

The installed Alpha 4 full Turnip APK launches on Ryan's SM-X916B with Android 16.
Ryan has confirmed that S Pen sculpt strokes work and respond to pressure on a
separate quad sphere in Sculpt Mode. These observations apply to the installed
upstream build. The changes below still require their own APK and device tests.

## Changes in our build

- Hold the S Pen side button and move to orbit using Blender's middle mouse binding.
  Tip contact cannot start a brush stroke or selection while navigating. Lift the
  tip before starting another stroke after navigation. Finger long press keeps
  context menus.
- Pause rendering while Android pauses the Activity or removes its native window.
- Shrink the native drawing surface when the keyboard appears, keeping console
  input visible instead of hidden behind the keyboard. Restore it when dismissed.
- Use application ID `org.blender.blender.tabs9ultra` and label **Blender Tab S9 Ultra**,
  so the working upstream app remains installed beside the test app.
- Bundle Turnip, the driver path used by the working baseline.
- Audit all packaged native libraries and APK alignment for 16 KB compatibility.

Selecting does not automatically drag an object: choose Move or Transform and
drag its handles. Sculpting needs Sculpt Mode, an active brush and enough mesh
vertices. Dragging the coloured axis gizmo at the top right also orbits the view.

## Build

Run **Build Blender Android - Tab S9 Ultra** under GitHub Actions. Choose `full`
for Cycles and additional features, or `lite` for modelling, sculpting, EEVEE
and Python. This recipe follows the pinned source's
[build instructions](https://github.com/simfeo/blender/blob/android-alpha-4/build_files/android/BUILDING.md).
It uses NDK r30 beta1 and the exact dependency submodule commits recorded by the
source, replacing the retired hand-built dependency pipeline.

Artifacts include the APK, SHA-256, source and recipe commits, dependency
commits and complete source patch. Apply that patch to the exact upstream
commit to reproduce our source changes. Blender's GPL applies; the Turnip
helper separately pins Mesa 26.2.3 and libadrenotools.

CI APKs are debuggable and signed with an ephemeral development key. Before
installing successive builds, re-sign locally with the same private key.
Private keys stay outside the repository and uploaded artifacts. These builds
are for testing, with no release publication configured.

## Device acceptance

Verify launch, scene save/reopen, side-button orbit in hover and contact, tip
release and cancellation, pressure, finger context menus, keyboard visibility,
split screen, background/resume and rotation on the physical tablet. Build
success alone does not verify these behaviours. Keep the working baseline
installed during testing.
