// Notifikasi sukses
function notifSukses(pesan) {
    Swal.fire({
        icon: 'success',
        title: 'Berhasil',
        text: pesan,
        timer: 2000,
        showConfirmButton: false
    });
}

// Notifikasi error
function notifError(pesan) {
    Swal.fire({
        icon: 'error',
        title: 'Gagal',
        text: pesan
    });
}

// Konfirmasi (mengembalikan Promise<boolean>)
async function konfirmasi(pesan, tombolYa = 'Ya, lanjutkan!') {
    const result = await Swal.fire({
        title: 'Apakah Anda yakin?',
        text: pesan,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc2626',
        cancelButtonColor: '#6b7280',
        confirmButtonText: tombolYa,
        cancelButtonText: 'Batal'
    });
    return result.isConfirmed;
}