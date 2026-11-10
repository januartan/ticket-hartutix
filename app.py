# ============================================================
# 1. IMPORT LIBRARY
# ============================================================

from flask import (  # noqa: I001
    Flask, flash, redirect, render_template,
    request, session, url_for
)

import mysql.connector 
import os
import shutil
import uuid

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename


# ============================================================
# 2. KONFIGURASI APLIKASI
# ============================================================

app = Flask(__name__)
app.secret_key = "tickethartutix_secret_key"

# Folder penyimpanan poster event
UPLOAD_FOLDER = os.path.join(
    app.root_path,
    'static',
    'uploads',
    'kelompok3', 
    'events'
)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Folder penyimpanan gambar tiket
TICKET_UPLOAD_FOLDER = os.path.join(
    app.root_path,
    'static',
    'uploads',
    'kelompok3',
    'tiket'
)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

# Membuat folder upload jika belum tersedia
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TICKET_UPLOAD_FOLDER, exist_ok=True)

# Folder penyimpanan foto profile kelompok 3
PROFILE_UPLOAD_FOLDER = os.path.join(
    app.root_path,
    'static',
    'uploads',
    'kelompok3',
    'profile'
)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

os.makedirs(PROFILE_UPLOAD_FOLDER, exist_ok=True)

# Format gambar yang diperbolehkan
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


# ============================================================
# 3. FUNGSI PENDUKUNG UPLOAD GAMBAR
# ============================================================

def allowed_file(filename):
    """Memeriksa format file gambar yang diunggah."""

    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# ============================================================
# 4. KONEKSI DATABASE
# ============================================================

def get_db_connection():
    """Menghubungkan aplikasi dengan database MySQL."""

    koneksi = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="tickethartutix"
    )

    return koneksi


# FUNGSI PENDUKUNG PROFILE 030

def ambil_daftar_profile030():
    koneksi = get_db_connection()
    cursor = koneksi.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM profile030
            ORDER BY id_profile030 ASC
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        koneksi.close()


def vendor_tersedia030(nama_vendor):
    koneksi = get_db_connection()
    cursor = koneksi.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id_profile030
            FROM profile030
            WHERE nama_profile030 = %s
              AND status_profile030 = 'Aktif'
        """, (nama_vendor,))

        return cursor.fetchone() is not None

    finally:
        cursor.close()
        koneksi.close()


# ============================================================
# 6. LOGIN ADMIN DAN CUSTOMER
# ============================================================

@app.route('/login-admin', methods=['GET', 'POST'])
def login_admin():

    if request.method == 'POST':

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        selected_role = request.form.get('login_role', 'admin')

        koneksi = get_db_connection()
        cursor = koneksi.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT * FROM users WHERE username = %s",
                (username,)
            )

            user = cursor.fetchone()

            # Memeriksa username dan password
            if user and check_password_hash(user['password'], password):

                # Memeriksa kesesuaian role yang dipilih
                if selected_role == 'admin' and user['role'] != 'admin':
                    return render_template(
                        'login_admin.html',
                        error='Akun Customer tidak memiliki hak akses sebagai Admin/Vendor.'
                    )

                if selected_role == 'customer' and user['role'] != 'customer':
                    return render_template(
                        'login_admin.html',
                        error='Akun Administrator tidak dapat masuk melalui portal Customer.'
                    )

                # Menghapus session sebelumnya
                session.clear()

                session['id_user'] = user['id_user']
                session['username'] = user['username']
                session['role'] = user['role']

                # Mengarahkan pengguna berdasarkan role
                if user['role'] == 'admin':
                    session['admin_login'] = True
                    return redirect(url_for('home'))

                elif user['role'] == 'customer':
                    session['customer_login'] = True
                    return redirect(url_for('halaman_customer'))

            # Jika username atau password salah
            return render_template(
                'login_admin.html',
                error='Username atau password salah!'
            )

        finally:
            cursor.close()
            koneksi.close()

    return render_template('login_admin.html')


# ============================================================
# 7. HALAMAN CUSTOMER
# ============================================================

# DASHBOARD CUSTOMER
@app.route('/customer')
def halaman_customer():

    if not session.get('customer_login'):
        return redirect(url_for('login_admin'))

    return render_template('customer_home.html')


# DAFTAR EVENT CUSTOMER
@app.route('/customer/event')
def customer_event():

    if not session.get('customer_login'):
        return redirect(url_for('login_admin'))

    koneksi = get_db_connection()
    cursor = koneksi.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM event017
            WHERE status_event017 = 'Aktif'
            ORDER BY tanggal_event017 ASC
        """)

        daftar_event = cursor.fetchall()

    finally:
        cursor.close()
        koneksi.close()

    return render_template(
        'customer_event.html',
        daftar_event=daftar_event
    )


# DAFTAR TIKET CUSTOMER
@app.route('/customer/tiket')
def customer_tiket():

    if not session.get('customer_login'):
        return redirect(url_for('login_admin'))

    koneksi = get_db_connection()
    cursor = koneksi.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                h.*,
                e.nama_band017,
                e.tanggal_event017,
                e.alamat_event017
            FROM harga_tiket028 AS h
            JOIN event017 AS e
                ON h.kode_event028 = e.kode_event017
            WHERE h.status_tiket028 = 'Aktif'
              AND e.status_event017 = 'Aktif'
            ORDER BY e.tanggal_event017 ASC
        """)

        daftar_tiket = cursor.fetchall()

    finally:
        cursor.close()
        koneksi.close()

    return render_template(
        'customer_tiket.html',
        daftar_tiket=daftar_tiket
    )


# ============================================================
# 8. LOGOUT
# ============================================================

@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('login_admin'))


# ============================================================
# 9. DASHBOARD ADMIN
# ============================================================

@app.route('/')
def home():

    if not session.get('admin_login'):
        return redirect(url_for('login_admin'))

    return render_template('home.html')


# ============================================================
# 10. PENGELOLAAN EVENT 017
# ============================================================

# MENAMPILKAN DATA EVENT
@app.route('/vendor/event')
def halaman_event017():

    if not session.get('admin_login'):
        return redirect(url_for('login_admin'))

    koneksi = get_db_connection() 
    cursor = koneksi.cursor(dictionary=True)

    #kode di bawah Asc untuk mengurutkan data
    cursor.execute(""" 
    SELECT * FROM event017
    ORDER BY id_event017 ASC  
""") 

    daftar_event017 = cursor.fetchall()

    cursor.close()
    koneksi.close()

    return render_template(
        'event.html',
        daftar_event017=daftar_event017,
        daftar_profile=ambil_daftar_profile030()
    )


# MENAMBAHKAN EVENT
@app.route('/vendor/event/tambah', methods=['POST'])
def tambah_event017():

    if not session.get('admin_login'):
        return redirect(url_for('login_admin'))

    # Mengambil data dari form
    kode = request.form.get('kode_event017', '').strip()
    band = request.form.get('nama_band017', '').strip()
    vendor = request.form.get('nama_vendor017', '').strip()
    tanggal = request.form.get('tanggal_event017', '')
    jadwal = request.form.get('jadwal_event017', '')
    alamat = request.form.get('alamat_event017', '').strip()
    status = request.form.get('status_event017', '')

    foto = request.files.get('foto_event017')

    # Memeriksa kelengkapan data
    if not all([kode, band, vendor, tanggal, jadwal, alamat, status]):
        flash('Semua field event wajib diisi!', 'error')
        return redirect(url_for('halaman_event017'))

    if not foto or foto.filename == '':
        flash('Poster event wajib diunggah!', 'error')
        return redirect(url_for('halaman_event017'))

    if not allowed_file(foto.filename):
        flash('Format poster harus PNG, JPG, JPEG, atau WEBP!', 'error')
        return redirect(url_for('halaman_event017'))

    if not vendor_tersedia030(vendor):
        flash('Nama vendor tidak ditemukan atau tidak aktif!', 'error')
        return redirect(url_for('halaman_event017'))

    koneksi = get_db_connection()
    cursor = koneksi.cursor(dictionary=True)

    lokasi_foto = None #untuk menyimpan lokasi file poster yang diunggah

    try:
        # Memeriksa kode event agar tidak duplikat
        cursor.execute(
            "SELECT kode_event017 FROM event017 WHERE kode_event017 = %s", #untuk memeriksa kode event pada database agar tidak duplikat
            (kode,)
        )

        if cursor.fetchone():
            flash('Kode event sudah digunakan!', 'error')
            return redirect(url_for('halaman_event017'))

        # Membuat nama file unik
        ekstensi = foto.filename.rsplit('.', 1)[1].lower()
        nama_file = f"kelompok3_{uuid.uuid4().hex}.{ekstensi}" 

        lokasi_foto = os.path.join(
            app.config['UPLOAD_FOLDER'], #untuk menyimpan lokasi file poster yang diunggah ke folder upload
            nama_file
        )

        foto.save(lokasi_foto) #untuk save file poster yang diunggah ke folder upload

        # Menyimpan data event ke database
        cursor.execute("""
            INSERT INTO event017 
            (
                kode_event017,
                nama_band017,
                nama_vendor017,
                tanggal_event017,
                jadwal_event017,
                alamat_event017,
                status_event017,
                foto_event017
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            kode,
            band,
            vendor,
            tanggal,
            jadwal,
            alamat,
            status,
            nama_file
        ))

        koneksi.commit() #menyimpan perubahan

        flash('Event dan poster berhasil ditambahkan!', 'success')

    except mysql.connector.Error as e: #untuk menangani error yang terjadi saat menyimpan data event ke database

        koneksi.rollback()

        if lokasi_foto and os.path.exists(lokasi_foto):
            try:
                os.remove(lokasi_foto)
            except OSError as cleanup_error:
                print(f'Poster gagal dibersihkan: {cleanup_error}')

        flash(f'Gagal menambahkan event: {e}', 'error')

    except Exception as e:  # noqa: BLE001

        koneksi.rollback()

        if lokasi_foto and os.path.exists(lokasi_foto):
            os.remove(lokasi_foto) #berfungsi menghapus foto pada folder static

        flash(f'Gagal mengunggah poster: {e}', 'error')

    finally:
        cursor.close() #untuk menutup koneksi ke database
        koneksi.close() 

    return redirect(url_for('halaman_event017'))


# FORM EDIT EVENT
@app.route('/vendor/event/edit/<string:kode_event017>')
def form_edit_event017(kode_event017):

    if not session.get('admin_login'):
        return redirect(url_for('login_admin'))

    koneksi = get_db_connection()
    cursor = koneksi.cursor(dictionary=True)

    cursor.execute(
    """
    SELECT *,
    TIME_FORMAT(jadwal_event017, '%H:%i') AS jadwal_edit017
    FROM event017
    WHERE kode_event017 = %s
    """,
    (kode_event017,)
)

    event = cursor.fetchone() #untuk mengambil 1 baris data 

    cursor.close()
    koneksi.close()

    if not event:
        return render_template('404.html'), 404

    return render_template(
        'edit_event.html',
        event017_data=event,
        daftar_profile=ambil_daftar_profile030()
    )


# MEMPERBARUI EVENT
@app.route('/vendor/event/update/<string:kode_event017>', methods=['POST'])
def update_event017(kode_event017):

    if not session.get('admin_login'):
        return redirect(url_for('login_admin'))

    koneksi = get_db_connection()
    cursor = koneksi.cursor(dictionary=True) 

    lokasi_foto_baru = None

    try:
        cursor.execute(
            "SELECT * FROM event017 WHERE kode_event017 = %s", #untuk mengambil data event berdasarkan kode_event017 dari database
            (kode_event017,)
        )

        event = cursor.fetchone()

        if not event:
            return render_template('404.html'), 404

        # Mengambil data terbaru dari form
        kode = request.form.get('kode_event017', '').strip()
        band = request.form.get('nama_band017', '').strip()
        vendor = request.form.get('nama_vendor017', '').strip()
        tanggal = request.form.get('tanggal_event017', '')
        jadwal = request.form.get('jadwal_event017', '')
        alamat = request.form.get('alamat_event017', '').strip()
        status = request.form.get('status_event017', '')

        foto = request.files.get('foto_event017')
        
        # Memeriksa apakah kode event digunakan oleh tiket
        if kode != kode_event017:

            cursor.execute("""
                SELECT id_tiket028
                FROM harga_tiket028
                WHERE kode_event028 = %s
                LIMIT 1
            """, (kode_event017,))

            tiket_terkait = cursor.fetchone()

            if tiket_terkait:
                flash(
                    'Kode event tidak bisa diubah karena masih memiliki detail tiket!',
                    'error'
                )
                return redirect(url_for(
                    'form_edit_event017',
                    kode_event017=kode_event017
                ))

            # Memeriksa apakah kode baru sudah digunakan event lain
            cursor.execute("""
                SELECT id_event017
                FROM event017
                WHERE kode_event017 = %s
            """, (kode,))

            kode_sudah_ada = cursor.fetchone()

            if kode_sudah_ada:
                flash('Kode event sudah digunakan!', 'error')
                return redirect(url_for(
                    'form_edit_event017',
                    kode_event017=kode_event017
                ))

        if not all([kode, band, vendor, tanggal, jadwal, alamat, status]):
            flash('Semua field event wajib diisi!', 'error')
            return redirect(url_for(
                'form_edit_event017',
                kode_event017=kode_event017
            ))

        if not vendor_tersedia030(vendor):
            flash('Nama vendor tidak ditemukan atau tidak aktif!', 'error')
            return redirect(url_for(
                'form_edit_event017',
                kode_event017=kode_event017
            ))
        
        # Secara default menggunakan poster lama
        nama_file = event['foto_event017']

        # Mengunggah poster baru jika dipilih
        if foto and foto.filename != '':

            if not allowed_file(foto.filename):
                flash('Format poster harus PNG, JPG, JPEG, atau WEBP!', 'error')
                return redirect(url_for(
                    'form_edit_event017',
                    kode_event017=kode_event017
                ))

            ekstensi = foto.filename.rsplit('.', 1)[1].lower()
            nama_file = f"kelompok3_{uuid.uuid4().hex}.{ekstensi}"

            lokasi_foto_baru = os.path.join(
                app.config['UPLOAD_FOLDER'],
                nama_file
            )

            foto.save(lokasi_foto_baru)


        # Memperbarui data event
        cursor.execute("""
            UPDATE event017
            SET kode_event017 = %s,
                nama_band017 = %s,
                nama_vendor017 = %s,
                tanggal_event017 = %s,
                jadwal_event017 = %s,
                alamat_event017 = %s,
                status_event017 = %s,
                foto_event017 = %s
            WHERE kode_event017 = %s
        """, (
            kode,
            band,
            vendor,
            tanggal,
            jadwal,
            alamat,
            status,
            nama_file,
            kode_event017
        ))

        koneksi.commit()

        # Menghapus poster lama setelah database berhasil diperbarui
        if lokasi_foto_baru and event['foto_event017']:

            lokasi_foto_lama = os.path.join(
                app.config['UPLOAD_FOLDER'],
                event['foto_event017']
            )

            if os.path.exists(lokasi_foto_lama): #untuk menghapus poster lama jika ada
                try:
                    os.remove(lokasi_foto_lama)
                except OSError as e:
                    print(f'Poster lama gagal dihapus: {e}')

        flash('Event berhasil diperbarui!', 'success')

    except mysql.connector.Error as e:

        koneksi.rollback()

        if lokasi_foto_baru and os.path.exists(lokasi_foto_baru):
            os.remove(lokasi_foto_baru)

        flash(f'Gagal memperbarui event: {e}', 'error')

    except Exception as e:  # noqa: BLE001

        koneksi.rollback()

        if lokasi_foto_baru and os.path.exists(lokasi_foto_baru):
            os.remove(lokasi_foto_baru)

        flash(f'Gagal memperbarui poster: {e}', 'error')

    finally:
        cursor.close()
        koneksi.close()

    return redirect(url_for('halaman_event017'))


# MENGHAPUS EVENT
@app.route('/vendor/event/hapus/<string:kode_event017>', methods=['POST'])
def hapus_event017(kode_event017):

    if not session.get('admin_login'):
        return redirect(url_for('login_admin'))

    koneksi = get_db_connection()
    cursor = koneksi.cursor(dictionary=True)

    try:
        # Memeriksa apakah event masih memiliki data tiket
        cursor.execute(
            """
            SELECT id_tiket028
            FROM harga_tiket028
            WHERE kode_event028 = %s
            LIMIT 1
            """,
            (kode_event017,)
        )

        if cursor.fetchone():
            flash(
                'Event tidak dapat dihapus karena masih memiliki data harga tiket!',
                'error'
            )
            return redirect(url_for('halaman_event017'))

        # Mengambil nama poster event
        cursor.execute(
            "SELECT foto_event017 FROM event017 WHERE kode_event017 = %s",
            (kode_event017,) 
        ) 

        event = cursor.fetchone()

        if not event:
            flash('Event tidak ditemukan!', 'error')
            return redirect(url_for('halaman_event017'))

        # Menghapus data event dari database
        cursor.execute(
            "DELETE FROM event017 WHERE kode_event017 = %s",
            (kode_event017,)
        )

        koneksi.commit()

        # Menghapus file poster dari folder
        if event['foto_event017']:

            lokasi_foto = os.path.join(
                app.config['UPLOAD_FOLDER'],
                event['foto_event017']
            )

            if os.path.exists(lokasi_foto):
                os.remove(lokasi_foto)

        flash('Event berhasil dihapus!', 'success')

    except Exception as e:  # noqa: BLE001

        koneksi.rollback()
        flash(f'Gagal menghapus event: {e}', 'error')

    finally:
        cursor.close()
        koneksi.close()

    return redirect(url_for('halaman_event017'))

    
# ============================================================
# 11. PENGELOLAAN PROFILE VENDOR 030
# ============================================================

# MENAMPILKAN DATA PROFILE
@app.route('/profile')
def halaman_profile030():

    if not session.get('admin_login'):
        return redirect(url_for('login_admin'))

    daftar_profile = ambil_daftar_profile030()


    return render_template(
        'profile.html',
        daftar_profile=daftar_profile
    )


# MENAMBAHKAN PROFILE
@app.route('/profile/tambah', methods=['POST'])
def tambah_profile030():

    if not session.get('admin_login'):
        return redirect(url_for('login_admin'))

    nama_profile030 = request.form.get(
        'nama_profile030', '').strip()

    jenis_usaha030 = request.form.get(
        'jenis_usaha030', '').strip()

    email_profile030 = request.form.get(
        'email_profile030', '').strip()

    telepon_profile030 = request.form.get(
        'telepon_profile030', '').strip()

    alamat_profile030 = request.form.get(
        'alamat_profile030', '').strip()

    status_profile030 = request.form.get(
        'status_profile030', '').strip()

    foto = request.files.get('foto_profile030')

    if not all([
        nama_profile030,
        jenis_usaha030,
        email_profile030,
        telepon_profile030,
        alamat_profile030,
        status_profile030
    ]):
        flash('Semua field profil wajib diisi!', 'error')
        return redirect(url_for('halaman_profile030'))

    if status_profile030 not in ('Aktif', 'Tidak Aktif'):
        flash('Status profil tidak valid!', 'error')
        return redirect(url_for('halaman_profile030'))

    if not foto or foto.filename == '':
        flash('Foto profil wajib diunggah!', 'error')
        return redirect(url_for('halaman_profile030'))

    if not allowed_file(foto.filename):
        flash('Format foto harus PNG, JPG, JPEG, atau WEBP!', 'error')
        return redirect(url_for('halaman_profile030'))

    koneksi = get_db_connection()
    cursor = koneksi.cursor()

    lokasi_foto = None

    try:
        ekstensi = foto.filename.rsplit('.', 1)[1].lower()

        nama_file = (
            f"kelompok3_profile030_{uuid.uuid4().hex}.{ekstensi}"
        )

        lokasi_foto = os.path.join(
            PROFILE_UPLOAD_FOLDER,
            nama_file
        )

        foto.save(lokasi_foto)

        cursor.execute("""
            INSERT INTO profile030
            (
                nama_profile030,
                jenis_usaha030,
                email_profile030,
                telepon_profile030,
                alamat_profile030,
                status_profile030,
                foto_profile030
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            nama_profile030,
            jenis_usaha030,
            email_profile030,
            telepon_profile030,
            alamat_profile030,
            status_profile030,
            nama_file
        ))

        koneksi.commit() #nyimpan perubahan

        flash('Profil vendor berhasil ditambahkan!', 'success')

    except Exception as e:  # noqa: BLE001
        koneksi.rollback()

        if lokasi_foto and os.path.exists(lokasi_foto):
            os.remove(lokasi_foto)

        flash(f'Gagal menambahkan profil: {e}', 'error')

    finally:
        cursor.close()
        koneksi.close()

    return redirect(url_for('halaman_profile030'))


# FORM EDIT PROFILE
@app.route('/profile/edit/<int:id_profile030>')
def form_edit_profile030(id_profile030):

    if not session.get('admin_login'):
        return redirect(url_for('login_admin'))

    koneksi = get_db_connection()
    cursor = koneksi.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM profile030
            WHERE id_profile030 = %s
        """, (id_profile030,))

        profil = cursor.fetchone()

    finally:
        cursor.close()
        koneksi.close()

    if not profil:
        return render_template('404.html'), 404

    return render_template(
        'edit_profile.html',
        profil_data=profil
    )


# MEMPERBARUI PROFILE
@app.route('/profile/update/<int:id_profile030>', methods=['POST'])
def update_profile030(id_profile030):

    if not session.get('admin_login'):
        return redirect(url_for('login_admin'))

    nama_profile030 = request.form.get(
        'nama_profile030', '').strip()

    jenis_usaha030 = request.form.get(
        'jenis_usaha030', '').strip()

    email_profile030 = request.form.get(
        'email_profile030', '').strip()

    telepon_profile030 = request.form.get(
        'telepon_profile030', '').strip()

    alamat_profile030 = request.form.get(
        'alamat_profile030', '').strip()

    status_profile030 = request.form.get(
        'status_profile030', '').strip()

    foto = request.files.get('foto_profile030')

    if not all([
        nama_profile030,
        jenis_usaha030,
        email_profile030,
        telepon_profile030,
        alamat_profile030,
        status_profile030
    ]):
        flash('Semua field profil wajib diisi!', 'error')
        return redirect(url_for(
            'form_edit_profile030',
            id_profile030=id_profile030
        ))

    if status_profile030 not in ('Aktif', 'Tidak Aktif'):
        flash('Status profil tidak valid!', 'error')
        return redirect(url_for(
            'form_edit_profile030',
            id_profile030=id_profile030
        ))

    if foto and foto.filename and not allowed_file(foto.filename):
        flash('Format foto harus PNG, JPG, JPEG, atau WEBP!', 'error')
        return redirect(url_for(
            'form_edit_profile030',
            id_profile030=id_profile030
        ))

    koneksi = get_db_connection()
    cursor = koneksi.cursor(dictionary=True)

    lokasi_foto_baru = None

    try:
        cursor.execute("""
            SELECT foto_profile030
            FROM profile030
            WHERE id_profile030 = %s
        """, (id_profile030,))

        profil = cursor.fetchone()

        if not profil:
            return render_template('404.html'), 404

        nama_file = profil['foto_profile030']

        # Jika ada foto baru yang diunggah
        if foto and foto.filename:

            ekstensi = foto.filename.rsplit('.', 1)[1].lower()

            nama_file = (
                f"kelompok3_profile030_{uuid.uuid4().hex}.{ekstensi}"
            )

            lokasi_foto_baru = os.path.join(
                PROFILE_UPLOAD_FOLDER,
                nama_file
            )

            foto.save(lokasi_foto_baru)

        cursor.execute("""
            UPDATE profile030
            SET
                nama_profile030 = %s,
                jenis_usaha030 = %s,
                email_profile030 = %s,
                telepon_profile030 = %s,
                alamat_profile030 = %s,
                status_profile030 = %s,
                foto_profile030 = %s
            WHERE id_profile030 = %s
        """, (
            nama_profile030,
            jenis_usaha030,
            email_profile030,
            telepon_profile030,
            alamat_profile030,
            status_profile030,
            nama_file,
            id_profile030
        ))

        koneksi.commit()

        # Menghapus foto lama setelah update berhasil
        if lokasi_foto_baru and profil['foto_profile030']:

            foto_lama = os.path.join(
                PROFILE_UPLOAD_FOLDER,
                os.path.basename(profil['foto_profile030'])
            )

            if os.path.isfile(foto_lama):
                os.remove(foto_lama)

        flash('Profil vendor berhasil diperbarui!', 'success')

    except Exception as e:  # noqa: BLE001
        koneksi.rollback()

        if lokasi_foto_baru and os.path.exists(lokasi_foto_baru):
            os.remove(lokasi_foto_baru)

        flash(f'Gagal memperbarui profil: {e}', 'error')

    finally:
        cursor.close()
        koneksi.close()

    return redirect(url_for('halaman_profile030'))


# MENGHAPUS PROFILE
@app.route('/profile/hapus/<int:id_profile030>', methods=['POST'])
def hapus_profile030(id_profile030):

    if not session.get('admin_login'):
        return redirect(url_for('login_admin'))

    koneksi = get_db_connection()
    cursor = koneksi.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT nama_profile030, foto_profile030
            FROM profile030
            WHERE id_profile030 = %s
        """, (id_profile030,))

        profil = cursor.fetchone()

        if not profil:
            flash('Profil vendor tidak ditemukan!', 'error')
            return redirect(url_for('halaman_profile030'))

        # Memeriksa apakah vendor masih digunakan oleh event
        cursor.execute("""
            SELECT kode_event017
            FROM event017
            WHERE nama_vendor017 = %s
            LIMIT 1
        """, (profil['nama_profile030'],))

        event = cursor.fetchone()

        if event:
            flash(
                'Profil tidak dapat dihapus karena masih digunakan oleh event!',
                'error'
            )
            return redirect(url_for('halaman_profile030'))

        cursor.execute("""
            DELETE FROM profile030
            WHERE id_profile030 = %s
        """, (id_profile030,))

        koneksi.commit()

        # Menghapus foto dari folder
        if profil['foto_profile030']:

            foto_path = os.path.join(
                PROFILE_UPLOAD_FOLDER,
                os.path.basename(profil['foto_profile030'])
            )

            if os.path.isfile(foto_path):
                os.remove(foto_path)

        flash('Profil vendor berhasil dihapus!', 'success')

    except Exception as e:  # noqa: BLE001
        koneksi.rollback()
        flash(f'Gagal menghapus profil: {e}', 'error')

    finally:
        cursor.close()
        koneksi.close()

    return redirect(url_for('halaman_profile030'))


# ============================================================
# 12. FUNGSI PENDUKUNG GAMBAR TIKET
# ============================================================

def _tiket_image_path028(filename):
    """Mengambil lokasi file gambar tiket."""

    if not filename:
        return None

    filename = os.path.basename(filename)

    if not allowed_file(filename):
        return None

    return os.path.join(
        TICKET_UPLOAD_FOLDER,
        filename
    )


def _tiket_image_url028(filename):
    """Mengubah lokasi gambar tiket menjadi URL static."""

    path = _tiket_image_path028(filename)

    if not path:
        return None

    return os.path.relpath(
        path,
        os.path.join(app.root_path, 'static')
    ).replace(os.sep, '/')


def _event_image_url028(filename):
    """Mengambil URL poster event."""

    if not filename:
        return None

    filename = os.path.basename(filename)

    if not allowed_file(filename):
        return None

    path = os.path.join(
        app.config['UPLOAD_FOLDER'],
        filename
    )

    return os.path.relpath(
        path,
        os.path.join(app.root_path, 'static')
    ).replace(os.sep, '/')


def _tiket_image_filename028(kode_event, ekstensi):
    """Membuat nama file gambar tiket yang unik."""

    kode_aman = secure_filename(kode_event) or 'event'

    return (
        f'{kode_aman}_tiket_{uuid.uuid4().hex}.{ekstensi}'
    )


def _save_ticket_image(foto, kode_event):
    """Menyimpan gambar tiket yang diunggah."""

    if not foto or not foto.filename:
        return None

    if not allowed_file(foto.filename):
        raise ValueError(
            'Format gambar harus PNG, JPG, JPEG, atau WEBP.'
        )

    ekstensi = foto.filename.rsplit('.', 1)[1].lower()

    nama_file = _tiket_image_filename028(
        kode_event,
        ekstensi
    )

    lokasi = os.path.join(
        TICKET_UPLOAD_FOLDER,
        nama_file
    )

    foto.save(lokasi)

    return nama_file, lokasi


def _copy_event_ticket_image(event, kode_event):
    """Menyalin poster event sebagai gambar tiket."""

    nama_poster = event.get('foto_event017')

    if not nama_poster:
        return None

    sumber = os.path.join(
        app.config['UPLOAD_FOLDER'],
        os.path.basename(nama_poster)
    )

    if not os.path.isfile(sumber):
        return None

    ekstensi = os.path.splitext(sumber)[1].lstrip('.').lower()

    if ekstensi not in ALLOWED_EXTENSIONS:
        raise ValueError(
            'Format poster event tidak didukung untuk gambar tiket.'
        )

    nama_file = _tiket_image_filename028(
        kode_event,
        ekstensi
    )

    tujuan = os.path.join(
        TICKET_UPLOAD_FOLDER,
        nama_file
    )

    shutil.copy2(sumber, tujuan)

    return nama_file, tujuan


# ============================================================
# 13. PENGELOLAAN HARGA TIKET 028
# ============================================================

# MENAMPILKAN DATA HARGA TIKET
@app.route('/vendor/detail')
def halaman_vendor():

    if not session.get('admin_login'):
        return redirect(url_for('login_admin'))

    koneksi = get_db_connection()
    cursor = koneksi.cursor(dictionary=True)

    try:
        # Mengambil data harga tiket dan informasi event
        cursor.execute("""
            SELECT
                h.*,
                e.nama_band017 AS nama_event_display,
                e.tanggal_event017,
                e.alamat_event017
            FROM harga_tiket028 AS h
            LEFT JOIN event017 AS e
                ON h.kode_event028 = e.kode_event017
            ORDER BY h.id_tiket028 ASC
        """)

        datatiket = cursor.fetchall()

        for harga in datatiket:
            harga['foto_tiket'] = _tiket_image_url028(
                harga.get('img_event028')
            )

        # Mengambil daftar event untuk pilihan form
        cursor.execute("""
            SELECT
                kode_event017,
                nama_band017,
                foto_event017
            FROM event017
            ORDER BY nama_band017 ASC
        """)

        daftar_event = cursor.fetchall()

    finally:
        cursor.close()
        koneksi.close()

    return render_template(
        'vendor_detail.html',
        datatiket=datatiket,
        daftar_event=daftar_event
    )


# MENAMBAHKAN HARGA TIKET
@app.route('/vendor/detail/tambah', methods=['POST'])
def tambah_harga028():

    if not session.get('admin_login'):
        return redirect(url_for('login_admin'))

    nama_tiket = request.form.get('nama_tiket028', '').strip()
    kode_event = request.form.get('kode_event028', '').strip()
    harga_text = request.form.get('harga_tiket028', '').strip()
    stok_text = request.form.get('stok_tiket028', '').strip()
    status = request.form.get('status_tiket028', '').strip()

    foto = request.files.get('foto_tiket028')

    # Memeriksa nilai harga dan stok
    try:
        harga_tiket = int(harga_text)
        stok_tiket = int(stok_text)

    except (ValueError, TypeError):
        flash(
            'Harga dan stok harus berupa angka yang valid.',
            'error'
        )
        return redirect(url_for('halaman_vendor'))

    if (
        not nama_tiket
        or not kode_event
        or harga_tiket < 0
        or stok_tiket < 0
        or status not in ('Aktif', 'Tidak Aktif')
    ):
        flash(
            'Lengkapi data harga tiket dengan nilai yang valid.',
            'error'
        )
        return redirect(url_for('halaman_vendor'))

    koneksi = get_db_connection()
    cursor = koneksi.cursor(dictionary=True)

    lokasi_foto = None

    try:
        # Memeriksa event yang dipilih
        cursor.execute(
            """
            SELECT nama_band017, foto_event017
            FROM event017
            WHERE kode_event017 = %s
            """,
            (kode_event,)
        )

        event = cursor.fetchone()

        if not event:
            flash('Event yang dipilih tidak ditemukan.', 'error')
            return redirect(url_for('halaman_vendor'))

        # Menyimpan data harga tiket
        cursor.execute("""
            INSERT INTO harga_tiket028
            (
                nama_tiket028,
                kode_event028,
                nama_event028,
                harga_tiket028,
                stok_tiket028,
                status_tiket028,
                img_event028
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            nama_tiket,
            kode_event,
            event['nama_band017'],
            harga_tiket,
            stok_tiket,
            status,
            None
        ))

        id_tiket_baru = cursor.lastrowid

        # Jika Admin mengunggah gambar sendiri
        if foto and foto.filename:

            nama_foto, lokasi_foto = _save_ticket_image(
                foto,
                kode_event
            )

        # Jika tidak, salin poster dari event
        else:

            salinan_foto = _copy_event_ticket_image(
                event,
                kode_event
            )

            if salinan_foto:
                nama_foto, lokasi_foto = salinan_foto

        # Menyimpan nama gambar ke database
        if lokasi_foto:

            cursor.execute(
                """
                UPDATE harga_tiket028
                SET img_event028 = %s
                WHERE id_tiket028 = %s
                """,
                (nama_foto, id_tiket_baru)
            )

        koneksi.commit()

        flash('Harga tiket berhasil ditambahkan.', 'success')

    except ValueError as e:

        koneksi.rollback()

        if lokasi_foto and os.path.exists(lokasi_foto):
            os.remove(lokasi_foto)

        flash(str(e), 'error')

    except (mysql.connector.Error, OSError) as e:

        koneksi.rollback()

        if lokasi_foto and os.path.exists(lokasi_foto):
            os.remove(lokasi_foto)

        flash(f'Gagal menambahkan harga tiket: {e}', 'error')

    finally:
        cursor.close()
        koneksi.close()

    return redirect(url_for('halaman_vendor'))


# FORM EDIT HARGA TIKET
@app.route('/vendor/detail/edit/<int:id_tiket028>')
def form_edit_harga(id_tiket028):

    if not session.get('admin_login'):
        return redirect(url_for('login_admin'))

    koneksi = get_db_connection()
    cursor = koneksi.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                h.*,
                e.nama_band017 AS nama_event_display,
                e.foto_event017 AS foto_event_source
            FROM harga_tiket028 AS h
            LEFT JOIN event017 AS e
                ON h.kode_event028 = e.kode_event017
            WHERE h.id_tiket028 = %s
        """, (id_tiket028,))

        harga = cursor.fetchone()

        if not harga:
            return render_template('404.html'), 404

        harga['foto_tiket'] = _tiket_image_url028(
            harga.get('img_event028')
        )

        harga['foto_event_preview'] = _event_image_url028(
            harga.get('foto_event_source')
        )

        cursor.execute("""
            SELECT
                kode_event017,
                nama_band017,
                foto_event017
            FROM event017
            ORDER BY nama_band017 ASC
        """)

        daftar_event = cursor.fetchall()

    finally:
        cursor.close()
        koneksi.close()

    return render_template(
        'edit_detail_vendor.html',
        harga_data=harga,
        daftar_event=daftar_event
    )


# MEMPERBARUI HARGA TIKET
@app.route('/vendor/detail/update/<int:id_tiket028>', methods=['POST'])
def update_harga(id_tiket028):

    if not session.get('admin_login'):
        return redirect(url_for('login_admin'))

    nama_tiket = request.form.get('nama_tiket028', '').strip()
    kode_event = request.form.get('kode_event028', '').strip()
    harga_text = request.form.get('harga_tiket028', '').strip()
    stok_text = request.form.get('stok_tiket028', '').strip()
    status = request.form.get('status_tiket028', '').strip()

    foto = request.files.get('foto_tiket028')

    try:
        harga_tiket = int(harga_text)
        stok_tiket = int(stok_text)

    except (ValueError, TypeError):
        flash(
            'Harga dan stok harus berupa angka yang valid.',
            'error'
        )
        return redirect(url_for(
            'form_edit_harga',
            id_tiket028=id_tiket028
        ))

    if (
        not nama_tiket
        or not kode_event
        or harga_tiket < 0
        or stok_tiket < 0
        or status not in ('Aktif', 'Tidak Aktif')
    ):
        flash(
            'Lengkapi data harga tiket dengan nilai yang valid.',
            'error'
        )
        return redirect(url_for(
            'form_edit_harga',
            id_tiket028=id_tiket028
        ))

    koneksi = get_db_connection()
    cursor = koneksi.cursor(dictionary=True)

    foto_baru = None
    gambar_diganti = False

    try:
        # Mengambil data tiket lama
        cursor.execute(
            """
            SELECT
                id_tiket028,
                kode_event028,
                img_event028
            FROM harga_tiket028
            WHERE id_tiket028 = %s
            """,
            (id_tiket028,)
        )

        tiket = cursor.fetchone()

        if not tiket:
            return render_template('404.html'), 404

        # Memeriksa event yang dipilih
        cursor.execute(
            """
            SELECT nama_band017, foto_event017
            FROM event017
            WHERE kode_event017 = %s
            """,
            (kode_event,)
        )

        event = cursor.fetchone()

        if not event:
            flash('Event yang dipilih tidak ditemukan.', 'error')
            return redirect(url_for(
                'form_edit_harga',
                id_tiket028=id_tiket028
            ))

        foto_lama_path = _tiket_image_path028(
            tiket['img_event028']
        )

        nama_foto = tiket['img_event028']

        # Jika Admin mengunggah gambar baru
        if foto and foto.filename:

            foto_baru = _save_ticket_image(
                foto,
                kode_event
            )

            nama_foto = foto_baru[0]
            gambar_diganti = True

        # Jika event diganti, gambar tiket mengikuti poster event baru
        elif tiket['kode_event028'] != kode_event:

            foto_baru = _copy_event_ticket_image(
                event,
                kode_event
            )

            nama_foto = foto_baru[0] if foto_baru else None
            gambar_diganti = True

        # Memperbarui data harga tiket
        cursor.execute("""
            UPDATE harga_tiket028
            SET nama_tiket028 = %s,
                kode_event028 = %s,
                nama_event028 = %s,
                harga_tiket028 = %s,
                stok_tiket028 = %s,
                status_tiket028 = %s,
                img_event028 = %s
            WHERE id_tiket028 = %s
        """, (
            nama_tiket,
            kode_event,
            event['nama_band017'],
            harga_tiket,
            stok_tiket,
            status,
            nama_foto,
            id_tiket028
        ))

        koneksi.commit()

        # Menghapus gambar lama jika gambar berhasil diganti
        if (
            gambar_diganti
            and foto_lama_path
            and os.path.isfile(foto_lama_path)
        ):
            try:
                os.remove(foto_lama_path)

            except OSError as e:
                flash(
                    f'Gambar lama tidak dapat dibersihkan: {e}',
                    'error'
                )

        flash('Harga tiket berhasil diperbarui.', 'success')

    except ValueError as e:

        koneksi.rollback()

        if foto_baru and os.path.exists(foto_baru[1]):
            os.remove(foto_baru[1])

        flash(str(e), 'error')

    except (mysql.connector.Error, OSError) as e:

        koneksi.rollback()

        if foto_baru and os.path.exists(foto_baru[1]):
            os.remove(foto_baru[1])

        flash(f'Gagal memperbarui harga tiket: {e}', 'error')

    finally:
        cursor.close()
        koneksi.close()

    return redirect(url_for('halaman_vendor'))


# MENGHAPUS HARGA TIKET
@app.route('/vendor/detail/hapus/<int:id_tiket028>', methods=['POST'])
def hapus_harga(id_tiket028):

    if not session.get('admin_login'):
        return redirect(url_for('login_admin'))

    koneksi = get_db_connection()
    cursor = koneksi.cursor(dictionary=True)

    try:
        # Mengambil nama gambar tiket
        cursor.execute(
            """
            SELECT img_event028
            FROM harga_tiket028
            WHERE id_tiket028 = %s
            """,
            (id_tiket028,)
        )

        tiket = cursor.fetchone()

        if not tiket:
            return render_template('404.html'), 404

        # Menghapus data tiket dari database
        cursor.execute(
            """
            DELETE FROM harga_tiket028
            WHERE id_tiket028 = %s
            """,
            (id_tiket028,)
        )

        koneksi.commit()

        # Menghapus gambar tiket dari folder
        foto_path = _tiket_image_path028(
            tiket['img_event028']
        )

        if foto_path and os.path.isfile(foto_path):

            try:
                os.remove(foto_path)

            except OSError as e:
                flash(
                    f'Harga terhapus, tetapi gambar tidak dapat dibersihkan: {e}',
                    'error'
                )

        flash('Harga tiket berhasil dihapus.', 'success')

    except mysql.connector.Error as e:

        koneksi.rollback()
        flash(f'Gagal menghapus harga tiket: {e}', 'error')

    finally:
        cursor.close()
        koneksi.close()

    return redirect(url_for('halaman_vendor'))


# ============================================================
# 14. HALAMAN ABOUT
# ============================================================

@app.route('/about')
def about():

    if not session.get('admin_login'):
        return redirect(url_for('login_admin'))

    return render_template('about.html')


# ============================================================
# 15. TEST KONEKSI DATABASE
# ============================================================

@app.route('/test-db')
def test_db():

    try:
        koneksi = get_db_connection()
        koneksi.close()

        return "Koneksi database berhasil!"

    except Exception as e:  # noqa: BLE001

        return f"Koneksi database gagal: {e}"


# ============================================================
# 16. MEMBUAT AKUN BAWAAN ADMIN DAN CUSTOMER
# ============================================================

def buat_akun_bawaan():

    akun = [ 
        ('admin017', 'Admin017@123', 'admin'),
        ('customer017', 'Customer017@123', 'customer')
    ]

    koneksi = get_db_connection() 
    cursor = koneksi.cursor(dictionary=True)  #\

    try:
        for username, password, role in akun: 

            # Memeriksa apakah username sudah tersedia
            cursor.execute(
                "SELECT id_user FROM users WHERE username = %s",
                (username,)
            )

            if not cursor.fetchone():

                # Mengubah password menjadi hash
                password_hash = generate_password_hash(password)

                # Menambahkan akun ke database
                cursor.execute("""
                    INSERT INTO users (username, password, role)
                    VALUES (%s, %s, %s)
                """, (
                    username,
                    password_hash,
                    role
                ))

        koneksi.commit()

        print("Akun Admin dan Customer berhasil diperiksa.")

    except Exception:

        koneksi.rollback() 
        raise

    finally:
        cursor.close()
        koneksi.close()


# ============================================================
# 17. MENJALANKAN APLIKASI
# ============================================================

if __name__ == '__main__':

    buat_akun_bawaan()

    app.run(
        debug=True,
        port=5001
    )