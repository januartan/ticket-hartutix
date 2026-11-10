// ============ HAPUS (DELETE) ============
document.querySelectorAll('.btn-hapus').forEach(function(btn) {
    btn.addEventListener('click', function() {
        hapusMahasiswa(this.dataset.id);
    });
});

async function hapusMahasiswa(id) {
    const yakin = await konfirmasi('Data yang dihapus tidak bisa dikembalikan!');
    if (!yakin) return;

    try {
        const response = await fetch(`/mahasiswa/${id}`, {
            method: 'DELETE'
        });

        const hasil = await response.json();

        if (response.ok) {
            document.getElementById(`row-${id}`).remove();
            notifSukses(hasil.pesan);
        } else {
            notifError(hasil.pesan || 'Gagal menghapus data');
        }
    } catch (err) {
        notifError('Terjadi kesalahan: ' + err.message);
    }
}