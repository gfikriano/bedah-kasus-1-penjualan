"""
Dashboard Streamlit - Bedah Kasus 1: Dataset Operasional Penjualan
Nama : Ganesia Alkhan Fikriano
NIM  : 241051019

Jalankan:  streamlit run app.py
Data    :  data_penjualan_sintetis.csv (satu folder dengan app.py). Jika tidak ada,
           data sintetis 1.000 baris dibuat otomatis dengan seed yang sama seperti di notebook.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------- Identitas & konstanta
NAMA, NIM = "Ganesia Alkhan Fikriano", "241051019"
BIRU, ORANYE, ABU, ABU_TUA = "#2E9BD6", "#F5A03A", "#7A7F87", "#4F5560"
BLUES = ["#08306B", "#08519C", "#2171B5", "#4292C6", "#6BAED6", "#9ECAE1", "#C6DBEF"]
HARGA, QTY = "Harga (Rp)", "Jumlah Terjual"
NAMA_BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
NAMA_HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

st.set_page_config(page_title=f"Dashboard Penjualan - {NIM}", page_icon="📊", layout="wide")

def buat_data_penjualan(n=1000, seed=241051019):
    """Dataset operasional penjualan sintetis.
    1 baris = penjualan 1 produk pada 1 tanggal (kombinasi Produk-Tanggal unik).
    Kolom: Produk, Kategori, Harga (Rp), Jumlah Terjual, Tanggal.
    """
    rng = np.random.default_rng(seed)

    # (produk, harga dasar Rp, rata-rata unit terjual per hari)
    katalog = {
        "Elektronik": [("Laptop", 8_500_000, 14), ("Smartphone", 3_200_000, 26),
                       ("Smartwatch", 1_250_000, 30), ("Headphone Bluetooth", 450_000, 60),
                       ("Power Bank", 250_000, 85), ("Mouse Wireless", 150_000, 90)],
        "Pendidikan": [("Buku Pelajaran", 75_000, 120), ("Novel Populer", 95_000, 80),
                       ("Kalkulator Ilmiah", 180_000, 50), ("Tas Ransel Sekolah", 250_000, 45),
                       ("Set Alat Tulis", 55_000, 140)],
        "Fashion": [("Kemeja Pria", 175_000, 55), ("Dress Wanita", 280_000, 40),
                    ("Sepatu Sneakers", 650_000, 28), ("Jaket Hoodie", 320_000, 38),
                    ("Kaos Polos", 85_000, 110)],
        "Makanan & Minuman": [("Kopi Arabika 1 kg", 185_000, 65), ("Teh Celup (Box)", 28_000, 170),
                              ("Mie Instan (Dus)", 115_000, 90), ("Madu Murni", 125_000, 55),
                              ("Keripik Singkong", 20_000, 200)],
        "Rumah Tangga": [("Rice Cooker", 450_000, 32), ("Blender", 380_000, 30),
                         ("Setrika", 250_000, 36), ("Set Panci", 520_000, 22),
                         ("Lampu LED (4 pcs)", 90_000, 95)],
        "Olahraga": [("Matras Yoga", 180_000, 42), ("Dumbbell 10 kg", 350_000, 26),
                     ("Sepatu Lari", 850_000, 20), ("Raket Badminton", 420_000, 24),
                     ("Botol Minum", 95_000, 85)],
        "Kesehatan & Kecantikan": [("Sunscreen", 85_000, 100), ("Serum Wajah", 160_000, 60),
                                   ("Vitamin C (Botol)", 110_000, 90), ("Masker Medis (Box)", 35_000, 150),
                                   ("Parfum", 320_000, 34)],
    }
    produk = pd.DataFrame(
        [(p, k, h, q) for k, items in katalog.items() for p, h, q in items],
        columns=["Produk", "Kategori", "harga_dasar", "qty_dasar"])
    produk["bobot"] = produk["qty_dasar"] ** 0.5   # barang murah lebih sering muncul

    # Pola waktu: musiman bulanan, akhir pekan, dan tanggal kembar (harbolnas)
    tanggal = pd.date_range("2024-01-01", "2024-12-31", freq="D")
    f_bulan = {1: .95, 2: .90, 3: 1.05, 4: 1.25, 5: .95, 6: .95,
               7: 1.10, 8: 1.00, 9: .95, 10: 1.00, 11: 1.20, 12: 1.30}
    kembar = {(3, 3): 1.8, (4, 4): 1.8, (5, 5): 1.8, (6, 6): 2.0, (7, 7): 2.0,
              (8, 8): 2.0, (9, 9): 2.5, (10, 10): 2.5, (11, 11): 4.0, (12, 12): 4.5}

    def bobot_tanggal(t):
        w = f_bulan[t.month]
        w *= 1.25 if t.dayofweek >= 5 else (1.10 if t.dayofweek == 4 else 1.0)
        return w * kembar.get((t.month, t.day), 1.0)

    bt = np.array([bobot_tanggal(t) for t in tanggal])
    bt = bt / bt.sum()

    def boost_kategori(kat, t):
        """Lonjakan permintaan khusus kategori (sekolah, Lebaran, tahun baru, akhir tahun)."""
        if kat == "Pendidikan":
            return 1.8 if t.month in (7, 8) else (1.3 if t.month == 1 else 1.0)
        if kat in ("Fashion", "Makanan & Minuman"):
            return 1.7 if pd.Timestamp("2024-03-15") <= t <= pd.Timestamp("2024-04-14") else 1.0
        if kat == "Olahraga":
            return 1.3 if t.month == 1 else 1.0
        if kat == "Elektronik":
            return 1.4 if t.month in (11, 12) else 1.0
        return 1.0

    baris, terpakai = [], set()
    while len(baris) < n:
        t = tanggal[rng.choice(len(tanggal), p=bt)]
        boost = np.array([boost_kategori(k, t) for k in produk["Kategori"]])
        p = produk["bobot"].to_numpy() * boost
        i = rng.choice(len(produk), p=p / p.sum())
        if (i, t) in terpakai:
            continue
        terpakai.add((i, t))

        dasar = produk.at[i, "harga_dasar"]
        hari_kembar = (t.month, t.day) in kembar
        # Harga: fluktuasi pasar + promo (lebih sering pada tanggal kembar)
        harga = dasar * rng.lognormal(0, 0.06)
        if rng.random() < (0.7 if hari_kembar else 0.08):
            harga *= rng.uniform(0.80, 0.92)
        langkah = 500 if harga < 100_000 else (1_000 if harga < 1_000_000 else 10_000)
        harga = int(round(harga / langkah) * langkah)

        # Jumlah terjual (bilangan bulat): Poisson dengan elastisitas harga dan musiman
        lam = produk.at[i, "qty_dasar"] * boost[i] * f_bulan[t.month] * (dasar / harga) ** 1.3
        lam *= 1.6 if hari_kembar else 1.0
        lam *= 1.10 if t.dayofweek >= 5 else 1.0
        lam *= rng.lognormal(0, 0.25)
        qty = max(1, int(rng.poisson(lam)))
        baris.append((produk.at[i, "Produk"], produk.at[i, "Kategori"], harga, qty, t))

    df = pd.DataFrame(baris, columns=["Produk", "Kategori", "Harga (Rp)", "Jumlah Terjual", "Tanggal"])
    return df.sort_values(["Tanggal", "Produk"]).reset_index(drop=True)


# ----------------------------------------------------------------------------- Gaya
st.markdown(f"""
<style>
.block-container {{ padding-top: 1.6rem; padding-bottom: 4.5rem; }}
.hdr {{ display:flex; align-items:stretch; gap:16px; margin-bottom:.4rem; }}
.hdr .stripe {{ display:flex; flex-direction:column; width:8px; border-radius:4px; overflow:hidden; }}
.hdr .stripe span {{ flex:1; }}
.hdr h1 {{ margin:0; padding:0; font-size:2rem; line-height:1.15; }}
.hdr p {{ margin:.25rem 0 0 0; color:#5b6068; }}
.hdr .idbox {{ margin-left:auto; text-align:right; padding:.5rem .9rem; border:1px solid #d9dce1; border-radius:8px; font-size:.92rem; line-height:1.45; }}
.tag {{ border-left:5px solid var(--c); padding:.35rem .8rem; margin:.2rem 0 .8rem 0; background:rgba(127,127,127,.08); border-radius:0 6px 6px 0; font-size:.93rem; }}
.footer-id {{ position:fixed; left:0; right:0; bottom:0; z-index:999; text-align:center; font-size:.82rem;
             padding:.4rem; background:rgba(255,255,255,.96); color:#444; border-top:1px solid #d9dce1; }}
.sid {{ border:1px solid #d9dce1; border-radius:8px; padding:.6rem .8rem; line-height:1.5; font-size:.92rem; }}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------------- Utilitas format
def id_num(x, d=0):
    """Angka gaya Indonesia: 1.234.567,89"""
    return f"{x:,.{d}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def rp(x):
    return "Rp " + id_num(x)


def rp_singkat(x):
    a = abs(x)
    if a >= 1e12:
        return f"Rp {id_num(x / 1e12, 2)} T"
    if a >= 1e9:
        return f"Rp {id_num(x / 1e9, 2)} M"
    if a >= 1e6:
        return f"Rp {id_num(x / 1e6, 1)} jt"
    return rp(x)


def tag(teks, warna):
    st.markdown(f'<div class="tag" style="--c:{warna}">{teks}</div>', unsafe_allow_html=True)


def rapikan(fig, tinggi=420, judul=None):
    fig.update_layout(template="plotly_white", height=tinggi, margin=dict(l=10, r=10, t=55 if judul else 25, b=10),
                      legend_title_text="", title=dict(text=judul, font=dict(size=15)) if judul else None)
    return fig


# ----------------------------------------------------------------------------- Data
KOLOM_WAJIB = ["Produk", "Kategori", HARGA, QTY, "Tanggal"]


@st.cache_data(show_spinner=False)
def muat_bawaan():
    csv = Path(__file__).with_name("data_penjualan_sintetis.csv")
    if csv.exists():
        return pd.read_csv(csv, parse_dates=["Tanggal"])
    return buat_data_penjualan(1000)


def siapkan(df):
    df = df.copy()
    df["Tanggal"] = pd.to_datetime(df["Tanggal"])
    df["Produk"], df["Kategori"] = df["Produk"].astype(str), df["Kategori"].astype(str)
    df[HARGA], df[QTY] = df[HARGA].astype("int64"), df[QTY].astype("int64")
    df["Pendapatan"] = df[HARGA] * df[QTY]
    df["Bulan_Nama"] = pd.Categorical(df["Tanggal"].dt.month.map(lambda m: NAMA_BULAN[m - 1]), NAMA_BULAN, ordered=True)
    df["Hari_Nama"] = pd.Categorical(df["Tanggal"].dt.dayofweek.map(lambda d: NAMA_HARI[d]), NAMA_HARI, ordered=True)
    return df


# ----------------------------------------------------------------------------- Sidebar
with st.sidebar:
    st.markdown(f'<div class="sid"><b>{NAMA}</b><br>NIM {NIM}</div>', unsafe_allow_html=True)
    st.markdown("### Filter data")

    data_mentah = muat_bawaan()
    with st.expander("Gunakan data lain (CSV)"):
        up = st.file_uploader("Unggah CSV dengan kolom: Produk, Kategori, Harga (Rp), Jumlah Terjual, Tanggal", type="csv")
        if up is not None:
            try:
                tmp = pd.read_csv(up, parse_dates=["Tanggal"])
                hilang = [k for k in KOLOM_WAJIB if k not in tmp.columns]
                if hilang:
                    st.error(f"Kolom belum lengkap, tidak ada: {', '.join(hilang)}. Memakai data bawaan.")
                else:
                    data_mentah = tmp
                    st.success(f"{len(tmp):,} baris dimuat.".replace(",", "."))
            except Exception as e:  # noqa: BLE001
                st.error(f"CSV tidak bisa dibaca ({e}). Memakai data bawaan.")

df = siapkan(data_mentah)

tmin, tmax = df["Tanggal"].min().date(), df["Tanggal"].max().date()
rentang = st.sidebar.date_input("Rentang tanggal", (tmin, tmax), min_value=tmin, max_value=tmax, format="DD/MM/YYYY")
t0, t1 = (rentang[0], rentang[1]) if isinstance(rentang, (tuple, list)) and len(rentang) == 2 else (tmin, tmax)

semua_kat = sorted(df["Kategori"].unique())
kat_pilih = st.sidebar.multiselect("Kategori", semua_kat, default=semua_kat)
opsi_produk = sorted(df.loc[df["Kategori"].isin(kat_pilih), "Produk"].unique())
produk_pilih = st.sidebar.multiselect("Produk (kosong = semua)", opsi_produk)

hmin, hmax = int(df[HARGA].min() // 1000 * 1000), int(-(-df[HARGA].max() // 1000) * 1000)   # kelipatan langkah slider
rng_harga = st.sidebar.slider("Harga (Rp)", hmin, hmax, (hmin, hmax), step=1000, format="%d")
qmin, qmax = int(df[QTY].min()), int(df[QTY].max())
rng_qty = st.sidebar.slider("Jumlah terjual (unit)", qmin, qmax, (qmin, qmax))

st.sidebar.markdown("### Pengaturan tampilan")
metrik = st.sidebar.radio("Ukuran utama", ["Pendapatan", QTY], horizontal=True,
                          help="Dipakai pada grafik tab Ringkasan dan Waktu.")
top_n = st.sidebar.slider("Top N produk", 3, 15, 8)

# ----------------------------------------------------------------------------- Filter
mask = (df["Tanggal"].dt.date.between(t0, t1) & df["Kategori"].isin(kat_pilih)
        & df[HARGA].between(*rng_harga) & df[QTY].between(*rng_qty))
if produk_pilih:
    mask &= df["Produk"].isin(produk_pilih)
f = df[mask]

# ----------------------------------------------------------------------------- Header
st.markdown(f"""
<div class="hdr">
  <div class="stripe"><span style="background:{BIRU}"></span><span style="background:{ORANYE}"></span><span style="background:{ABU}"></span></div>
  <div><h1>Dashboard Operasional Penjualan</h1>
       <p>Bedah Kasus 1. Data sintetis 1.000 baris, divisualisasikan sesuai tipe data tiap kolom.</p></div>
  <div class="idbox"><b>{NAMA}</b><br>NIM {NIM}</div>
</div>
""", unsafe_allow_html=True)
st.caption("Kode warna mengikuti gambar tugas: biru untuk data kategorik, oranye untuk numerik, abu-abu untuk waktu.")
st.markdown(f'<div class="footer-id">{NAMA} &nbsp;|&nbsp; NIM {NIM} &nbsp;|&nbsp; Bedah Kasus 1: Dataset Operasional Penjualan</div>',
            unsafe_allow_html=True)

if f.empty:
    st.warning("Tidak ada data yang cocok dengan filter. Longgarkan rentang tanggal, kategori, atau slider harga/unit di sidebar.")
    st.stop()

# ----------------------------------------------------------------------------- KPI
k = st.columns(5)
k[0].metric("Total pendapatan", rp_singkat(f["Pendapatan"].sum()),
            f"{f['Pendapatan'].sum() / df['Pendapatan'].sum():.0%} dari seluruh data", delta_color="off")
k[1].metric("Total unit terjual", id_num(f[QTY].sum()))
k[2].metric("Jumlah record", id_num(len(f)), f"{f['Produk'].nunique()} produk", delta_color="off")
k[3].metric("Rata-rata harga", rp(f[HARGA].mean()), f"median {rp_singkat(f[HARGA].median())}", delta_color="off")
k[4].metric("Rata-rata unit per record", id_num(f[QTY].mean(), 1), f"median {f[QTY].median():.0f}", delta_color="off")

tabs = st.tabs(["Ringkasan", "Kategorik", "Harga", "Jumlah Terjual", "Waktu", "Hubungan", "Data"])

# ============================================================================= TAB 1 RINGKASAN
with tabs[0]:
    c1, c2 = st.columns([1, 1.25])
    por_kat = f.groupby("Kategori")[metrik].sum().sort_values(ascending=False).reset_index()
    fig = px.pie(por_kat, names="Kategori", values=metrik, hole=.5, color_discrete_sequence=BLUES)
    fig.update_traces(textinfo="percent", sort=False)
    c1.plotly_chart(rapikan(fig, 400, f"Komposisi {metrik.lower()} per kategori"), width="stretch", key="ring_pie")

    por_prod = f.groupby(["Produk", "Kategori"])[metrik].sum().nlargest(top_n).reset_index().sort_values(metrik)
    fig = px.bar(por_prod, x=metrik, y="Produk", orientation="h", color="Kategori", color_discrete_sequence=BLUES,
                 text=por_prod[metrik].map(lambda v: id_num(v / 1e6, 0) + " jt" if metrik == "Pendapatan" else id_num(v)))
    fig.update_traces(textposition="outside", cliponaxis=False)
    c2.plotly_chart(rapikan(fig, 400, f"Top {top_n} produk berdasarkan {metrik.lower()}"), width="stretch", key="ring_bar")

    kat_top = por_kat.iloc[0]
    pr_top = por_prod.iloc[-1]
    h_pk = f.groupby("Bulan_Nama", observed=True)[metrik].sum()
    st.info(f"**Temuan cepat.** Kategori terbesar: **{kat_top['Kategori']}** ({kat_top[metrik] / por_kat[metrik].sum():.0%} dari total). "
            f"Produk teratas: **{pr_top['Produk']}**. Bulan puncak: **{h_pk.idxmax()}**, bulan terendah: **{h_pk.idxmin()}**.")

# ============================================================================= TAB 2 KATEGORIK
with tabs[1]:
    tag("<b>Kategorik (Nominal)</b>: Produk dan Kategori. Visualisasi yang sesuai: Bar chart atau Pie chart.", BIRU)
    a, b, c = st.columns(3)
    var = a.radio("Variabel", ["Kategori", "Produk"], horizontal=True)
    ukuran = b.radio("Ukuran", ["Jumlah record", "Total unit", "Total pendapatan"], horizontal=True)
    jenis = c.radio("Jenis grafik", ["Bar chart", "Pie chart"], horizontal=True)

    agg = f.groupby(var).agg(**{"Jumlah record": ("Produk", "size"), "Total unit": (QTY, "sum"),
                                "Total pendapatan": ("Pendapatan", "sum")}).sort_values(ukuran, ascending=False)
    tampil = agg[[ukuran]].head(top_n) if var == "Produk" else agg[[ukuran]].copy()
    if var == "Produk" and jenis == "Pie chart" and len(agg) > top_n:
        tampil.loc["Lainnya"] = agg[ukuran].iloc[top_n:].sum()
    tampil = tampil.reset_index()

    if jenis == "Bar chart":
        d = tampil.sort_values(ukuran)
        fig = px.bar(d, x=ukuran, y=var, orientation="h", color_discrete_sequence=[BIRU], text=ukuran)
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
    else:
        fig = px.pie(tampil, names=var, values=ukuran, hole=.45, color_discrete_sequence=BLUES + ["#B9BCC2"] * 20)
        fig.update_traces(textinfo="percent+label", sort=False)
    ket = f" (Top {top_n})" if var == "Produk" else ""
    c1, c2 = st.columns([1.1, 1])
    c1.plotly_chart(rapikan(fig, 460, f"{ukuran} per {var}{ket}"), width="stretch", key="kat_main")

    tm = px.treemap(f, path=["Kategori", "Produk"], values="Pendapatan", color="Kategori", color_discrete_sequence=BLUES)
    c2.plotly_chart(rapikan(tm, 460, "Treemap pendapatan: Kategori > Produk"), width="stretch", key="kat_tree")

    st.markdown("**Tabel ringkasan** (modus = baris pertama menurut jumlah record)")
    ring = agg.assign(**{"% pendapatan": agg["Total pendapatan"] / agg["Total pendapatan"].sum() * 100}).reset_index()
    st.dataframe(ring, hide_index=True, width="stretch", column_config={
        "Total unit": st.column_config.NumberColumn(format="%d"),
        "Total pendapatan": st.column_config.NumberColumn(format="Rp %d"),
        "% pendapatan": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100)})

# ============================================================================= TAB 3 HARGA
with tabs[2]:
    tag("<b>Numerik kontinu (Rasio)</b>: Harga (Rp), memiliki nol absolut. Visualisasi yang sesuai: Histogram.", ORANYE)
    a, b, c = st.columns(3)
    bins = a.slider("Jumlah bin histogram", 10, 100, 40, key="bins_h")
    log_h = b.toggle("Skala log10 (harga sangat miring)", value=False, key="log_h")
    per_kat_h = c.toggle("Warnai per kategori", value=False, key="kat_h")

    d = f.assign(**{"log10(Harga)": np.log10(f[HARGA])}) if log_h else f
    x = "log10(Harga)" if log_h else HARGA
    fig = px.histogram(d, x=x, nbins=bins, color="Kategori" if per_kat_h else None, marginal="box",
                       color_discrete_sequence=px.colors.qualitative.Set2 if per_kat_h else [ORANYE], barmode="stack")
    fig.add_vline(x=d[x].mean(), line_dash="dash", line_color="#C0392B")
    fig.add_vline(x=d[x].median(), line_dash="dash", line_color="#27AE60")
    c1, c2 = st.columns([1.2, 1])
    c1.plotly_chart(rapikan(fig, 470, "Histogram Harga"), width="stretch", key="h_hist")
    c1.caption("Garis putus-putus merah = mean, hijau = median.")

    fig = px.box(f, x="Kategori", y=HARGA, log_y=True, color_discrete_sequence=[ORANYE], points="outliers")
    fig.update_xaxes(categoryorder="median ascending")
    c2.plotly_chart(rapikan(fig, 470, "Sebaran harga per kategori (skala log)"), width="stretch", key="h_box")

    s = f[HARGA]
    q1, q3 = s.quantile([.25, .75])
    m = st.columns(5)
    m[0].metric("Mean", rp(s.mean()))
    m[1].metric("Median", rp(s.median()))
    m[2].metric("Simpangan baku", rp(s.std()) if len(s) > 1 else "-")
    m[3].metric("Skewness", f"{s.skew():.2f}" if len(s) > 2 else "-", help="> 0: miring ke kanan (ekor panjang di harga tinggi)")
    m[4].metric("IQR", rp(q3 - q1))
    desk = s.describe(percentiles=[.05, .25, .5, .75, .95]).to_frame("Harga (Rp)").T
    st.dataframe(desk.style.format("{:,.0f}"), width="stretch")

# ============================================================================= TAB 4 QTY
with tabs[3]:
    tag("<b>Numerik diskrit (Rasio)</b>: Jumlah Terjual, hasil perhitungan barang bulat. Visualisasi yang sesuai: bar/histogram bilangan bulat.", ORANYE)
    a, b = st.columns(2)
    lebar = a.slider("Lebar kelas (unit)", 1, 50, 10, key="bin_q")
    per_kat_q = b.toggle("Warnai per kategori", value=False, key="kat_q")
    fig = px.histogram(f, x=QTY, color="Kategori" if per_kat_q else None, marginal="box", barmode="stack",
                       color_discrete_sequence=px.colors.qualitative.Set2 if per_kat_q else [ORANYE])
    fig.update_traces(xbins=dict(size=lebar), selector=dict(type="histogram"))
    c1, c2 = st.columns([1.2, 1])
    c1.plotly_chart(rapikan(fig, 460, f"Distribusi Jumlah Terjual (kelas = {lebar} unit)"), width="stretch", key="q_hist")

    rata = f.groupby("Kategori")[QTY].agg(["mean", "std", "count"]).reset_index().sort_values("mean")
    rata["ci95"] = 1.96 * rata["std"].fillna(0) / np.sqrt(rata["count"])
    fig = px.bar(rata, x="mean", y="Kategori", orientation="h", error_x="ci95", color_discrete_sequence=["#F8C382"],
                 labels={"mean": "Rata-rata unit per record"})
    c2.plotly_chart(rapikan(fig, 460, "Rata-rata unit per kategori (95% CI)"), width="stretch", key="q_bar")

    q = f[QTY]
    m = st.columns(5)
    m[0].metric("Mean", id_num(q.mean(), 1))
    m[1].metric("Median", id_num(q.median()))
    m[2].metric("Modus", id_num(q.mode().iloc[0]))
    m[3].metric("Skewness", f"{q.skew():.2f}" if len(q) > 2 else "-")
    m[4].metric("Varians / mean", f"{q.var() / q.mean():.1f}" if len(q) > 1 else "-",
                help="Nilai jauh di atas 1 berarti overdispersi: laju penjualan antar produk sangat berbeda.")
    st.dataframe(q.describe(percentiles=[.05, .25, .5, .75, .95]).to_frame(QTY).T.style.format("{:,.1f}"), width="stretch")

# ============================================================================= TAB 5 WAKTU
with tabs[4]:
    tag("<b>Waktu (Interval)</b>: Tanggal. Visualisasi yang sesuai: Line chart untuk melihat tren waktu.", ABU)
    a, b, c = st.columns(3)
    gran = a.radio("Granularitas", ["Harian", "Mingguan", "Bulanan"], horizontal=True, index=1)
    ma = b.toggle("Garis rata-rata bergerak 7 hari (khusus harian)", value=True)
    pisah = c.toggle("Pisahkan per kategori", value=False)
    rule = {"Harian": "D", "Mingguan": "W", "Bulanan": "MS"}[gran]

    if pisah:
        s = f.groupby([pd.Grouper(key="Tanggal", freq=rule), "Kategori"])[metrik].sum().reset_index()
        fig = px.line(s, x="Tanggal", y=metrik, color="Kategori", markers=gran != "Harian", color_discrete_sequence=px.colors.qualitative.Safe)
    else:
        s = f.set_index("Tanggal")[metrik].resample(rule).sum().reset_index()
        fig = px.line(s, x="Tanggal", y=metrik, markers=gran != "Harian", color_discrete_sequence=[ABU])
        if gran == "Harian" and ma:
            fig.update_traces(line=dict(color="#B9BCC2", width=1))
            fig.add_trace(go.Scatter(x=s["Tanggal"], y=s[metrik].rolling(7, center=True, min_periods=1).mean(),
                                     mode="lines", name="Rata-rata 7 hari", line=dict(color=ABU_TUA, width=3)))
        else:
            fig.update_traces(line=dict(width=3))
    fig.update_xaxes(rangeslider_visible=True)
    st.plotly_chart(rapikan(fig, 460, f"Tren {metrik.lower()} ({gran.lower()})"), width="stretch", key="w_line")

    c1, c2 = st.columns(2)
    hr = f.groupby("Hari_Nama", observed=True)[metrik].sum().reindex(NAMA_HARI).reset_index()
    hr["Jenis"] = np.where(hr["Hari_Nama"].isin(["Sabtu", "Minggu"]), "Akhir pekan", "Hari kerja")
    fig = px.bar(hr, x="Hari_Nama", y=metrik, color="Jenis", color_discrete_map={"Hari kerja": ABU, "Akhir pekan": ABU_TUA})
    fig.update_xaxes(title="")
    c1.plotly_chart(rapikan(fig, 400, f"{metrik} per hari dalam seminggu"), width="stretch", key="w_hari")

    pt = f.pivot_table(index="Kategori", columns="Bulan_Nama", values=metrik, aggfunc="sum", observed=True)
    pt = pt.reindex(columns=NAMA_BULAN).dropna(axis=1, how="all")
    skala = 1e6 if metrik == "Pendapatan" else 1
    fig = px.imshow(pt / skala, text_auto=".0f", color_continuous_scale="Greys", aspect="auto",
                    labels=dict(color="juta Rp" if skala > 1 else "unit"))
    fig.update_xaxes(title="")
    fig.update_yaxes(title="")
    c2.plotly_chart(rapikan(fig, 400, "Heatmap Kategori x Bulan" + (" (juta Rp)" if skala > 1 else " (unit)")), width="stretch", key="w_heat")

# ============================================================================= TAB 6 HUBUNGAN
with tabs[5]:
    tag("<b>Hubungan antar variabel</b>: Harga vs Jumlah Terjual. Korelasi Spearman dipakai karena harga sangat miring.", ORANYE)
    a, b = st.columns(2)
    lx = a.toggle("Sumbu X (harga) skala log", value=True)
    ly = b.toggle("Sumbu Y (unit) skala log", value=True)
    fig = px.scatter(f, x=HARGA, y=QTY, color="Kategori", log_x=lx, log_y=ly, opacity=.75,
                     hover_data=["Produk", "Tanggal"], color_discrete_sequence=px.colors.qualitative.Safe)
    c1, c2 = st.columns([1.3, 1])
    c1.plotly_chart(rapikan(fig, 470, "Harga vs Jumlah Terjual"), width="stretch", key="r_sc")

    if len(f) > 2:
        cor = f[[HARGA, QTY, "Pendapatan"]].corr(method="spearman")
        fig = px.imshow(cor, text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale="RdBu_r")
        c2.plotly_chart(rapikan(fig, 470, "Korelasi Spearman"), width="stretch", key="r_cor")
        st.metric("Spearman rho (Harga, Jumlah Terjual)", f"{cor.loc[HARGA, QTY]:+.2f}",
                  help="Negatif: produk yang lebih mahal cenderung terjual lebih sedikit.")
    else:
        c2.info("Data terlalu sedikit untuk menghitung korelasi.")

# ============================================================================= TAB 7 DATA
with tabs[6]:
    st.markdown(f"**{id_num(len(f))} baris** sesuai filter dari {id_num(len(df))} baris total.")
    st.dataframe(f[KOLOM_WAJIB + ["Pendapatan"]].sort_values("Tanggal"), hide_index=True, width="stretch", column_config={
        "Tanggal": st.column_config.DateColumn(format="DD/MM/YY"),
        HARGA: st.column_config.NumberColumn(format="%d"),
        "Pendapatan": st.column_config.NumberColumn(format="%d")})
    st.download_button("Unduh data terfilter (CSV)", f[KOLOM_WAJIB].to_csv(index=False).encode("utf-8"),
                       file_name="data_penjualan_terfilter.csv", mime="text/csv")

    st.markdown("**Kamus data dan pilihan visualisasi**")
    st.dataframe(pd.DataFrame({
        "Kolom": ["Produk", "Kategori", HARGA, QTY, "Tanggal"],
        "Tipe / skala": ["Kategorik - Nominal", "Kategorik - Nominal", "Numerik kontinu - Rasio", "Numerik diskrit - Rasio", "Waktu - Interval"],
        "Contoh": ["Laptop", "Elektronik", "8.500.000", "45", "01/01/24"],
        "Visualisasi": ["Bar / Pie", "Bar / Pie", "Histogram", "Bar / Histogram bilangan bulat", "Line chart"]}),
        hide_index=True, width="stretch")
