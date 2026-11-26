"""
Pemodelan Aksesibilitas Jaringan Logistik Perikanan Tangkap Pesisir Kabupaten Cilacap
Kerangka Kerja: Operational Spatial Data Mining Framework (OSDMF - Flow & Distribution Layer)
Tim Penyusun  : Eky Febriansyah, Ibrahim Khafid Yourdani, Dava Riski Kurniawan
Program Studi : Teknik Informatika, Universitas Muhammadiyah Purwokerto (2026)
"""

from collections import Counter
import osmnx as ox
import networkx as nx
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString

# ==============================================================================
# 1. KONFIGURASI WILAYAH STUDI & SIMPUL LOGISTIK (3 TPI -> 4 PASAR UTAMA)
# ==============================================================================
CENTER_POINT = (-7.7120, 109.0260)
RADIUS_M = 6500
CRS_GEO = "EPSG:4326"
CRS_UTM = "EPSG:32749"  # WGS 84 / UTM Zone 49S
PEAK_HOUR_FACTOR = 1.45  # Faktor kongesti jam sibuk pelelangan pagi (05.30-08.30 WIB)

TPI_DATA = [
    {"id": "TPI_01", "nama": "TPI PPS Cilacap", "lat": -7.7265, "lon": 109.0238},
    {"id": "TPI_02", "nama": "TPI Sentolokawat", "lat": -7.7378, "lon": 109.0135},
    {"id": "TPI_03", "nama": "TPI Tegalkamulyan", "lat": -7.7125, "lon": 109.0355},
]

PASAR_DATA = [
    {"id": "PSR_01", "nama": "Pasar Gede Cilacap", "lat": -7.7289, "lon": 109.0112},
    {"id": "PSR_02", "nama": "Pasar Sidodadi", "lat": -7.7176, "lon": 109.0152},
    {"id": "PSR_03", "nama": "Pasar Tanjungsari", "lat": -7.7058, "lon": 109.0265},
    {"id": "PSR_04", "nama": "Pasar Gumilir", "lat": -7.6745, "lon": 109.0462},
]

# Kalibrasi kecepatan standar ruas jalan perkotaan & pesisir Indonesia (km/jam)
SPEED_BY_HIGHWAY = {
    "trunk": 60.0,
    "trunk_link": 50.0,
    "primary": 50.0,
    "primary_link": 45.0,
    "secondary": 45.0,
    "secondary_link": 40.0,
    "tertiary": 40.0,
    "tertiary_link": 35.0,
    "unclassified": 35.0,
    "residential": 30.0,
    "living_street": 20.0,
    "service": 25.0,
}


def resolve_highway_speed(highway_val) -> float:
    """Mengembalikan kecepatan kalibrasi (km/jam) berdasarkan kelas jalan OSM."""
    if isinstance(highway_val, list):
        speeds = [SPEED_BY_HIGHWAY.get(h, 35.0) for h in highway_val]
        return max(speeds) if speeds else 35.0
    return SPEED_BY_HIGHWAY.get(str(highway_val), 35.0)


def main():
    # --------------------------------------------------------------------------
    # TAHAP 1: AKUISISI DATA SPASIAL OPENSTREETMAP
    # --------------------------------------------------------------------------
    print("[1/5] Mengunduh jaringan jalan kendaraan bermotor OpenStreetMap...")
    G_raw = ox.graph_from_point(
        CENTER_POINT, dist=RADIUS_M, network_type="drive", simplify=True
    )

    # --------------------------------------------------------------------------
    # TAHAP 2: KONSTRUKSI TOPOLOGI GRAF & PEMBOBOTAN IMPEDANSI WAKTU TEMPUH
    # --------------------------------------------------------------------------
    print("[2/5] Menyaring komponen terhubung kuat terbesar & kalibrasi bobot...")
    G = ox.truncate.largest_component(G_raw, strongly=True)

    for u, v, k, data in G.edges(keys=True, data=True):
        speed_kph = resolve_highway_speed(data.get("highway", "unclassified"))
        length_m = float(data.get("length", 0.0))
        travel_time_sec = length_m / (speed_kph * 1000.0 / 3600.0)
        data["speed_kph"] = speed_kph
        data["travel_time"] = travel_time_sec

    gdf_tpi = gpd.GeoDataFrame(
        TPI_DATA,
        geometry=[Point(d["lon"], d["lat"]) for d in TPI_DATA],
        crs=CRS_GEO,
    )
    gdf_pasar = gpd.GeoDataFrame(
        PASAR_DATA,
        geometry=[Point(d["lon"], d["lat"]) for d in PASAR_DATA],
        crs=CRS_GEO,
    )

    gdf_tpi["node_id"] = ox.distance.nearest_nodes(
        G, X=gdf_tpi["lon"].values, Y=gdf_tpi["lat"].values
    )
    gdf_pasar["node_id"] = ox.distance.nearest_nodes(
        G, X=gdf_pasar["lon"].values, Y=gdf_pasar["lat"].values
    )

    # --------------------------------------------------------------------------
    # TAHAP 3: PEMODELAN RUTE TERCEPAT (DIJKSTRA) & SIMULASI JAM SIBUK
    # --------------------------------------------------------------------------
    print("[3/5] Menghitung 12 rute optimal Origin-Destination (Dijkstra)...")
    route_records = []
    edge_counter = Counter()

    for _, tpi in gdf_tpi.iterrows():
        for _, psr in gdf_pasar.iterrows():
            path_nodes = nx.shortest_path(
                G, source=tpi["node_id"], target=psr["node_id"], weight="travel_time"
            )
            total_length_m = 0.0
            total_time_sec = 0.0
            line_coords = []

            for idx in range(len(path_nodes) - 1):
                u, v = path_nodes[idx], path_nodes[idx + 1]
                # Pilih multi-edge dengan waktu tempuh tercepat
                edge_dict = G.get_edge_data(u, v)
                best_key = min(edge_dict, key=lambda k: edge_dict[k]["travel_time"])
                edata = edge_dict[best_key]

                total_length_m += float(edata["length"])
                total_time_sec += float(edata["travel_time"])
                edge_counter[(u, v)] += 1

                if "geometry" in edata:
                    seg_coords = list(edata["geometry"].coords)
                    if idx > 0 and line_coords and line_coords[-1] == seg_coords[0]:
                        line_coords.extend(seg_coords[1:])
                    else:
                        line_coords.extend(seg_coords)
                else:
                    p_u = (G.nodes[u]["x"], G.nodes[u]["y"])
                    p_v = (G.nodes[v]["x"], G.nodes[v]["y"])
                    if not line_coords:
                        line_coords.append(p_u)
                    line_coords.append(p_v)

            jarak_km = round(total_length_m / 1000.0, 2)
            waktu_normal_menit = round(total_time_sec / 60.0, 2)
            waktu_sibuk_menit = round(waktu_normal_menit * PEAK_HOUR_FACTOR, 2)
            kec_rata2_kmh = round(
                (total_length_m / 1000.0) / (total_time_sec / 3600.0), 1
            )

            route_records.append(
                {
                    "Asal_TPI": tpi["nama"],
                    "Tujuan_Pasar": psr["nama"],
                    "Jarak_km": jarak_km,
                    "Waktu_Normal_menit": waktu_normal_menit,
                    "Waktu_Jam_Sibuk_menit": waktu_sibuk_menit,
                    "Kecepatan_Rata2_kmh": kec_rata2_kmh,
                    "geometry": LineString(line_coords),
                }
            )

    gdf_rute = gpd.GeoDataFrame(route_records, crs=CRS_GEO)

    # --------------------------------------------------------------------------
    # TAHAP 4: DETEKSI KORIDOR KRITIS (BOTTLENECK OVERLAY)
    # --------------------------------------------------------------------------
    print("[4/5] Mengidentifikasi segmen koridor kritis (bottleneck)...")
    bottleneck_records = []
    for (u, v), freq in edge_counter.most_common():
        if freq >= 4:
            edge_dict = G.get_edge_data(u, v)
            best_key = min(edge_dict, key=lambda k: edge_dict[k]["travel_time"])
            edata = edge_dict[best_key]

            raw_name = edata.get("name", "Jalan Lokal/Kolektor")
            if isinstance(raw_name, list):
                nama_jalan = " / ".join(str(n) for n in raw_name)
            elif pd.isna(raw_name) or not str(raw_name).strip():
                nama_jalan = "Jalan Lokal/Kolektor"
            else:
                nama_jalan = str(raw_name)

            geom = edata.get(
                "geometry",
                LineString(
                    [(G.nodes[u]["x"], G.nodes[u]["y"]), (G.nodes[v]["x"], G.nodes[v]["y"])]
                ),
            )
            bottleneck_records.append(
                {
                    "u": u,
                    "v": v,
                    "nama_jalan": nama_jalan,
                    "panjang_m": float(edata["length"]),
                    "frekuensi": int(freq),
                    "geometry": geom,
                }
            )

    gdf_bottleneck = gpd.GeoDataFrame(bottleneck_records, crs=CRS_GEO)

    # --------------------------------------------------------------------------
    # TAHAP 5: EKSPOR BASIS DATA SPASIAL GEOPACKAGE (5 LAYER) & MATRIKS CSV
    # --------------------------------------------------------------------------
    print("[5/5] Menyimpan luaran GeoPackage (5 layer) dan CSV...")
    _, gdf_edges = ox.graph_to_gdfs(G)
    gdf_edges_clean = gdf_edges.reset_index()[
        ["u", "v", "key", "name", "highway", "length", "speed_kph", "travel_time", "geometry"]
    ].copy()
    for col in ["name", "highway"]:
        gdf_edges_clean[col] = gdf_edges_clean[col].apply(
            lambda x: ", ".join(map(str, x)) if isinstance(x, list) else ("" if pd.isna(x) else str(x))
        )

    gpkg_out = "Hasil_Aksesibilitas_TPI_Cilacap.gpkg"
    csv_out = "Tabel_Aksesibilitas_TPI_Cilacap.csv"

    gdf_edges_clean.to_file(gpkg_out, layer="jaringan_jalan", driver="GPKG")
    gdf_tpi[["id", "nama", "lat", "lon", "geometry"]].to_file(
        gpkg_out, layer="titik_tpi", driver="GPKG"
    )
    gdf_pasar[["id", "nama", "lat", "lon", "geometry"]].to_file(
        gpkg_out, layer="titik_pasar", driver="GPKG"
    )
    gdf_rute.to_file(gpkg_out, layer="rute_tercepat", driver="GPKG")
    gdf_bottleneck.to_file(gpkg_out, layer="koridor_bottleneck", driver="GPKG")

    gdf_rute.drop(columns=["geometry"]).to_csv(csv_out, index=False)
    print(f"Selesai! Luaran tersimpan ke '{gpkg_out}' dan '{csv_out}'.")


if __name__ == "__main__":
    main()
