import GOSTrocks.rasterMisc as rMisc
import pandas as pd


def calculate_admin_pop(
    city, admin_bounds, popR, city_id="eFUA_ID", city_name="eFUA_name"
):
    """_summary_

    Parameters
    ----------
    city_shape : _type_
        _description_
    admin_bounds : _type_
        _description_
    popR : _type_
        _description_
    """

    # Identify admin regions that intersect with the FUA, clip them, and calculate zonal stats
    sel_admin = admin_bounds.loc[admin_bounds.intersects(city["geometry"])].copy()
    sel_admin["geometry"] = sel_admin["geometry"].apply(
        lambda x: x.intersection(city["geometry"])
    )
    cur_zonal = rMisc.zonalStats(sel_admin, popR, minVal=0)
    cur_zonal = pd.DataFrame(cur_zonal, columns=["SUM", "MIN", "MAX", "MEAN"])
    cur_zonal["per_city_pop"] = cur_zonal["SUM"] / cur_zonal["SUM"].sum()

    # For those intersecting admin regions, calculate the percentage of their population outside the city
    sel_admin = admin_bounds.loc[admin_bounds.intersects(city["geometry"])].copy()
    total_pop = rMisc.zonalStats(sel_admin, popR, minVal=0)
    total_pop = pd.DataFrame(total_pop, columns=["SUM", "MIN", "MAX", "MEAN"])
    sel_admin["geometry"] = sel_admin["geometry"].apply(
        lambda x: x.difference(city["geometry"])
    )
    not_city_pop = rMisc.zonalStats(sel_admin, popR, minVal=0)
    not_city_pop = pd.DataFrame(not_city_pop, columns=["SUM", "MIN", "MAX", "MEAN"])
    not_city_pop["admin_pop"] = total_pop["SUM"]
    not_city_pop["per_not_city"] = not_city_pop["SUM"] / not_city_pop["admin_pop"]

    # Concat results
    admin_res = pd.DataFrame(sel_admin.drop(columns=["geometry"]).copy())
    admin_res = pd.concat(
        [
            admin_res.reset_index(),
            cur_zonal.drop(["SUM", "MIN", "MAX", "MEAN"], axis=1),
            not_city_pop.drop(["admin_pop", "SUM", "MIN", "MAX", "MEAN"], axis=1),
        ],
        axis=1,
    )
    admin_res["city_id"] = city[city_id]
    admin_res["city_name"] = city[city_name]
    return admin_res
