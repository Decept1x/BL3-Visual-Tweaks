from mods_base import build_mod #type: ignore
from ui_utils import show_hud_message #type: ignore
from typing import Any #type: ignore
import unrealsdk #type: ignore
from unrealsdk import make_struct, find_all, find_object, find_class, construct_object #type: ignore
from mods_base import get_pc, hook, keybind, build_mod, ENGINE, SliderOption, BoolOption #type: ignore
from unrealsdk.hooks import Type, add_hook, Block, remove_hook, inject_next_call, prevent_hooking_direct_calls #type: ignore
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct #type: ignore

map_name: str = ""
station: str = ""
counter: int = 1
spawn_location = None
spawn_rotation = None
travel_station_fallback: str = ""
takedown_maps: list[str] = ["Raid_P", "GuardianTakedown_P"]

projected_size_multiplier = SliderOption(
    "Projected Shield Size Multiplier",
    175,
    0,
    200,
    True,
    description="Changes the size of the projected shield in front of the player"
)

def apply_post_process(obj: UObject, args: WrappedStruct, _3: Any, func: BoundFunction) -> None:
    obj.PostProcessComponent.Settings.EdgeDetectionEnable = False

def shield_break_start(obj: UObject, args: WrappedStruct, _3: Any, func: BoundFunction) -> None:
    # remove shield break effect
    obj.ShieldBreakFeedback = None

def shield_break_end(obj: UObject, args: WrappedStruct, _3: Any, func: BoundFunction) -> None:
    # replace shield break effect
    obj.ShieldBreakFeedback = find_object("object", "/Game/Gear/Shields/_Design/Feedback/FBData_ShieldBreak.FBData_ShieldBreak")

@hook("/Script/OakGame.Shield:OnOwnerCrouched", Type.PRE)
def projected_size(obj: UObject, args: WrappedStruct, _3: Any, func: BoundFunction) -> None:
    if obj.ProjectedShield.AttachChildren[1].RelativeScale3D.X == projected_size_multiplier.value / 100:
        return
    obj.ProjectedShield.AttachChildren[1].RelativeScale3D = make_struct("Vector", X=projected_size_multiplier.value / 100, Y=projected_size_multiplier.value / 100, Z=projected_size_multiplier.value / 100)

def bloom_override(setting, new_value):
    if new_value is True:
        find_class("KismetSystemLibrary").ClassDefaultObject.ExecuteConsoleCommand(get_pc(), "r.BloomQuality 0|r.LensFlareQuality 0|r.DefaultFeature.LensFlare 0|r.DefaultFeature.Bloom 0", get_pc())
    else:
        find_class("KismetSystemLibrary").ClassDefaultObject.ExecuteConsoleCommand(get_pc(), "r.BloomQuality 5|r.LensFlareQuality 2|r.DefaultFeature.LensFlare 0|r.DefaultFeature.Bloom 1", get_pc())

def shield_break_override(setting, new_value):
    if new_value is True:
        add_hook("/Script/OakGame.Shield:OnShieldDepleted", Type.PRE, "shield_break_start", shield_break_start)
        add_hook("/Script/OakGame.Shield:OnShieldDepleted", Type.POST, "shield_break_end", shield_break_end)
    else:
        remove_hook("/Script/OakGame.Shield:OnShieldDepleted", Type.PRE, "shield_break_start")
        remove_hook("/Script/OakGame.Shield:OnShieldDepleted", Type.PRE, "shield_break_end")

def black_outlines_override(setting, new_value):
    if new_value is True:
        add_hook("/Game/Classes/TimeOfDay/BP_TimeOfDay_Base.BP_TimeOfDay_Base_C:ReceiveBeginPlay", Type.POST, "apply_post_process", apply_post_process)
        for x in find_all("PostProcessComponent", False):
            if "Maps" in str(x):
                x.Settings.EdgeDetectionEnable = False
    else:
        remove_hook("/Script/Engine.ActorComponent:ReceiveBeginPlay", Type.POST, "apply_post_process")
        for x in find_all("PostProcessComponent", False):
            if "Maps" in str(x):
                x.Settings.EdgeDetectionEnable = True

def screen_percentage_override(setting, new_value):
    find_class("KismetSystemLibrary").ClassDefaultObject.ExecuteConsoleCommand(get_pc(), f"r.ScreenPercentage {new_value}", get_pc())

bloom_override_option = BoolOption(
    "Disable Bloom",
    False,
    "Yes",
    "No",
    on_change=bloom_override,
    description="Disables bloom effects in game"
)

shield_break_override_option = BoolOption(
    "Disable Shield Break Effect",
    False,
    "Yes",
    "No",
    on_change=shield_break_override,
    description="Disables shield break effects in game"
)

black_outlines_override_option = BoolOption(
    "Disable Black Outlines",
    False,
    "Yes",
    "No",
    on_change=black_outlines_override,
    description="Disables the black outlines"
)

screen_percentage_multiplier = SliderOption(
    "Resolution Scale Multiplier",
    100,
    0,
    100,
    True,
    on_change=screen_percentage_override,
    description="Changes the resolution scale (same as in-game option but allows for exact values)"
)

build_mod(options=[black_outlines_override_option, bloom_override_option, shield_break_override_option, projected_size_multiplier, screen_percentage_multiplier], hooks=[projected_size])