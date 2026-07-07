from account_rules import (
    generate_pulte_ad_name,
    generate_touchstone_ad_name,
    generate_elv_ad_name
)

def generate_ad_name(
        account,
        rule,
        placement_name,
        dimension,
        creative_name,
        state_map):

    if rule == "Placement Name = Ad Name":
        return placement_name

    if rule == "Creative Name = Ad Name":
        return creative_name

    if rule == "Dimension = Ad Name":
        return dimension

    if account == "Pulte":
        return generate_pulte_ad_name(placement_name)

    if account == "Touchstone Energy":
        return generate_touchstone_ad_name(placement_name)

    if account == "Anthem / Elevance":
        return generate_elv_ad_name(
            placement_name,
            dimension,
            state_map
        )

    return placement_name
