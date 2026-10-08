#!/usr/bin/env python3
"""Apply reviewed Tab S9 Ultra changes to the pinned Alpha 4 source."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--version-code", type=int, default=1)
    args = parser.parse_args()
    root = args.source

    def replace(path, old, new):
        target = root / path
        content = target.read_text(encoding="utf-8")
        count = content.count(old)
        if count != 1:
            raise SystemExit(f"{path}: expected one baseline match, found {count}")
        target.write_text(content.replace(old, new, 1), encoding="utf-8", newline="\n")

    pen = "intern/ghost/intern/GHOST_SystemAndroid.cc"
    replace(pen,
        "  /* S Pen side button: independent right-click, in hover or contact. */\n"
        "  const bool side = (AMotionEvent_getButtonState(event) &\n"
        "                     AMOTION_EVENT_BUTTON_STYLUS_PRIMARY) != 0;\n",
        "  /* S Pen side button navigates with middle mouse. Releasing proximity or\n"
        "   * cancelling must release it even if Android still reports the button.\n"
        "   * A contact stroke ends before navigation starts; it does not restart\n"
        "   * until a fresh tip-down after navigation, avoiding accidental sculpt. */\n"
        "  const bool side = tablet.Active != GHOST_kTabletModeNone && !hover_exit &&\n"
        "                    action != AMOTION_EVENT_ACTION_CANCEL &&\n"
        "                    (AMotionEvent_getButtonState(event) &\n"
        "                     AMOTION_EVENT_BUTTON_STYLUS_PRIMARY) != 0;\n"
        "  if (side && touch_button_down_) {\n"
        "    touchSendButton(touch_button_, GHOST_kEventButtonUp);\n"
        "  }\n")
    replace(pen,
        "    buttons_.set(GHOST_kButtonMaskRight, side);",
        "    buttons_.set(GHOST_kButtonMaskMiddle, side);")
    replace(pen,
        "        GHOST_kButtonMaskRight,\n        tablet));",
        "        GHOST_kButtonMaskMiddle,\n        tablet));")
    replace(pen,
        "      if (is_stylus) {\n        touchSendButton(GHOST_kButtonMaskLeft, GHOST_kEventButtonDown);\n      }",
        "      if (is_stylus) {\n"
        "        if (!side) {\n"
        "          touchSendButton(GHOST_kButtonMaskLeft, GHOST_kEventButtonDown);\n"
        "        }\n      }")
    # End a contact stroke before the first cursor movement of navigation.
    # Keep the middle-button press after the cursor move, at the correct tip.
    target = root / pen
    content = target.read_text(encoding="utf-8")
    cursor_start = content.index("  /* Cursor tracks the tip whether touching or hovering")
    side_start = content.index("  /* S Pen side button navigates with middle mouse.")
    side_end = content.index("  if (side != stylus_button_down_)", side_start)
    content = (content[:cursor_start] + content[side_start:side_end] +
               content[cursor_start:side_start] + content[side_end:])
    target.write_text(content, encoding="utf-8", newline="\n")
    replace(pen,
        "void GHOST_SystemAndroid::handleWindowFocus(bool gained)\n{\n  if (!window_) {\n    return;\n  }",
        "void GHOST_SystemAndroid::handleWindowFocus(bool gained)\n{\n  if (!window_) {\n    return;\n  }\n"
        "  if (!gained && stylus_button_down_) {\n"
        "    stylus_button_down_ = false;\n"
        "    buttons_.set(GHOST_kButtonMaskMiddle, false);\n"
        "    pushEvent(std::make_unique<GHOST_EventButton>(\n"
        "        getMilliSeconds(), GHOST_kEventButtonUp, window_,\n"
        "        GHOST_kButtonMaskMiddle, touch_tablet_));\n  }")

    lifecycle = "intern/ghost/intern/GHOST_AndroidMain.cc"
    replace(lifecycle,
        "static bool g_blender_launched = false;",
        "static bool g_blender_launched = false;\n"
        "static bool g_has_native_window = false;\nstatic bool g_paused = true;")
    replace(lifecycle,
        "  switch (cmd) {\n    case APP_CMD_GAINED_FOCUS:",
        "  switch (cmd) {\n"
        "    case APP_CMD_RESUME:\n      g_paused = false;\n      break;\n"
        "    case APP_CMD_PAUSE:\n    case APP_CMD_STOP:\n"
        "      g_paused = true;\n"
        "      if (GHOST_ISystem::getSystem()) {\n"
        "        android_system()->handleWindowFocus(false);\n      }\n      break;\n\n"
        "    case APP_CMD_GAINED_FOCUS:")
    replace(lifecycle,
        "    case APP_CMD_INIT_WINDOW:\n      if (!g_blender_launched) {",
        "    case APP_CMD_INIT_WINDOW:\n"
        "      g_has_native_window = app->window != nullptr;\n"
        "      if (!g_blender_launched) {")
    replace(lifecycle,
        "    case APP_CMD_TERM_WINDOW:\n      if (GHOST_ISystem::getSystem()) {",
        "    case APP_CMD_TERM_WINDOW:\n      g_has_native_window = false;\n"
        "      if (GHOST_ISystem::getSystem()) {")
    ready = "g_context && g_has_native_window && !g_paused && app->window"
    replace(lifecycle, "int timeout = g_context ? 0 : -1;", f"int timeout = ({ready}) ? 0 : -1;")
    replace(lifecycle,
        "      if (g_context) {\n        timeout = 0;\n      }",
        f"      timeout = ({ready}) ? 0 : -1;")
    replace(lifecycle,
        "    if (g_context) {\n      blender::WM_main_loop_body(g_context);",
        f"    if ({ready}) {{\n      blender::WM_main_loop_body(g_context);")
    replace(lifecycle,
        "/* Block until the window exists (and Blender is launched); afterwards never\n"
        "     * block, so we fall through to render every frame.",
        "/* Block while paused or without a live window; render while active.")

    manifest = "build_files/android/apk/app/src/main/AndroidManifest.xml"
    replace(manifest, '    package="org.blender.blender">',
        '    package="org.blender.blender.tabs9ultra"\n'
        f'    android:versionCode="{args.version_code}"\n'
        f'    android:versionName="5.3.0 Alpha4 Tab S9 Ultra build {args.version_code}">')
    target = root / manifest
    target.write_text(target.read_text(encoding="utf-8").replace(
        'android:label="Blender"', 'android:label="Blender Tab S9 Ultra"'), encoding="utf-8", newline="\n")
    replace(manifest, '            android:launchMode="singleTask"\n',
        '            android:launchMode="singleTask"\n'
        '            android:resizeableActivity="true"\n'
        '            android:windowSoftInputMode="adjustNothing"\n')
    # Immersive NativeActivity renders behind the IME. Explicitly shrink the
    # content's SurfaceView using IME insets; Android sends WINDOW_RESIZED so
    # Blender recalculates its editor layout and input coordinates together.
    java = "build_files/android/apk/app/src/main/java/org/blender/blender/BlenderActivity.java"
    replace(java, "import android.view.ViewGroup;", "import android.view.ViewGroup;\nimport android.view.WindowInsets;")
    replace(java,
        "    addContentView(inputView, new ViewGroup.LayoutParams(1, 1));",
        "    addContentView(inputView, new ViewGroup.LayoutParams(1, 1));\n"
        "    final View content = findViewById(android.R.id.content);\n"
        "    final int padLeft = content.getPaddingLeft();\n"
        "    final int padTop = content.getPaddingTop();\n"
        "    final int padRight = content.getPaddingRight();\n"
        "    final int padBottom = content.getPaddingBottom();\n"
        "    content.setOnApplyWindowInsetsListener((view, insets) -> {\n"
        "      int keyboardHeight = insets.getInsets(WindowInsets.Type.ime()).bottom;\n"
        "      view.setPadding(padLeft, padTop, padRight, padBottom + keyboardHeight);\n"
        "      return insets;\n"
        "    });\n"
        "    content.requestApplyInsets();")
    # Keep Java and JNI namespaces: the fully qualified Activity is independent
    # of the manifest application ID, allowing both tablet apps to coexist.
    replace("build_files/android/build_apk.sh",
        "unset ANDROID_HOME ANDROID_NDK_ROOT ANDROID_NDK_HOME",
        "# Honour the SDK/NDK paths supplied by the caller, including CI.")
    # build.py starts a login shell, which may reset PATH and bypass the CI
    # ninja wrapper. Cap these nested build invocations explicitly as well.
    path = root / "build_files/android/build_apk.sh"
    text = path.read_text(encoding="utf-8")
    if text.count("ninja -C") != 4:
        raise SystemExit("Unexpected ninja invocation count in build_apk.sh")
    path.write_text(text.replace("ninja -C", 'ninja -j "${BLENDER_ANDROID_JOBS:-3}" -C'),
                    encoding="utf-8", newline="\n")
    replace("build_files/android/apk/package.sh",
        '"$BT/zipalign" -f -p 4 "$OUT" "$STAGE/blender-aligned.apk"',
        '"$BT/zipalign" -f -P 16 4 "$OUT" "$STAGE/blender-aligned.apk"')
    print("Applied S Pen, Android lifecycle, application ID and packaging changes.")


if __name__ == "__main__":
    main()
