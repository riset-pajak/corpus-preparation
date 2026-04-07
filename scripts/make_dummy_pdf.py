# type: ignore
"""Buat PDF dummy mirip dokumen regulasi pajak untuk end-to-end test."""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import textwrap
import sys

pdf_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/PMK-99-dummy.pdf"

class PageBuilder:
    def __init__(self, canvas_obj):
        self.c = canvas_obj
        self.y = 780

    def add(self, text: str, size: int = 11, bold: bool = False):
        if bold:
            self.c.setFont('Helvetica-Bold', size)
        else:
            self.c.setFont('Helvetica', size)
        lines = textwrap.wrap(text, width=90)
        for line in lines:
            if self.y < 40:
                self.c.showPage()
                if bold:
                    self.c.setFont('Helvetica-Bold', size)
                else:
                    self.c.setFont('Helvetica', size)
                self.y = 760
            self.c.drawString(72, self.y, line)
            self.y -= size * 1.4


c = canvas.Canvas(pdf_path, pagesize=letter)
p = PageBuilder(c)

p.add("PERATURAN MENTERI KEUANGAN", 11, True)
p.add("NOMOR 99/PMK.03/2024", 10, True)
p.add("TENTANG", 9)
p.add("KETENTUAN PEMOTONGAN PPh PASAL 21 ATAU PAJAK PENGHASILAN PASAL 22", 10, True)
p.add("", 8)

p.add("Pasal 1", 11, True)
p.add("Dalam Peraturan Menteri Keuangan ini yang dimaksud dengan PPh Pasal 21 atau PPh Pasal 22 atas penghasilan yang diterima atau diperoleh karyawan yang bersifat tetap adalah pajak penghasilan yang dipotong atas penghasilan berupa gaji, upah, tunjangan, honorarium, dan pembayaran lain dengan nama dan dalam bentuk apapun yang berkaitan dengan pekerjaan atau jasa yang dilakukan oleh orang pribadi sebagai wajib pajak dalam negeri.", 10)

p.add("Pasal 2", 11, True)
p.add("Pemotongan PPh Pasal 21 atau PPh Pasal 22 dilakukan oleh pemberi kerja atas penghasilan yang dibayarkan kepada karyawan dengan menggunakan tarif berdasarkan Pasal 17 ayat (1) huruf a Undang-Undang Pajak Penghasilan.", 10)

p.add("Pasal 3", 11, True)
p.add("(1) Penghasilan Kena Pajak bagi Wajib Pajak Orang Pribadi Dalam Negeri yang tidak mempunyai NPWP dikenai tarif sebesar 20% lebih tinggi dari tarif yang ditetapkan sebagaimana dimaksud dalam Pasal 17 ayat (1) huruf a Undang-Undang Pajak Penghasilan.", 10)
p.add("(2) Penentuan Penghasilan Kena Pajak bagi Wajib Pajak Orang Pribadi Dalam Negeri yang telah mempunyai NPWP dihitung atas dasar penghasilan bruto per bulan dikurangi pengurang yang diperkenankan.", 10)

p.add("Pasal 4", 11, True)
p.add("(1) Ketentuan mengenai PPh Pasal 22 atas impor barang tertentu diatur lebih lanjut dalam Peraturan Direktur Jenderal Pajak.", 10)
p.add("(2) Tata cara pemotongan dan penyetoran PPh Pasal 22 mengikuti ketentuan yang berlaku umum mengenai Ketentuan Umum dan Tata Cara Perpajakan.", 10)

p.add("Pasal 5", 11, True)
p.add("Ketentuan mengenai Bea Materai atas dokumen perjanjian kerja dan surat perjanjian lainnya yang berkaitan dengan hubungan kerja mengikuti ketentuan dalam Undang-Undang Bea Materai.", 10)

p.add("Pasal 6", 11, True)
p.add("(1) Pajak Pertambahan Nilai atas barang kena pajak yang diserahkan oleh pengusaha kena pajak tidak termasuk dalam dasar pengenaan PPh Pasal 21.", 10)
p.add("(2) Apabila penyerahan barang kena pajak tersebut bersamaan dengan pajak yang terutang, maka dasar pengenaan pajaknya adalah jumlah yang diterima dikurangi PPN.", 10)

p.add("Pasal 7", 11, True)
p.add("Penyampaian Surat Pemberitahuan Masa PPh Pasal 21 dilakukan paling lambat tanggal 20 bulan berikutnya setelah masa pajak berakhir, melalui sistem e-Bupot Unifikasi.", 10)

p.add("Pasal 8", 11, True)
p.add("Peraturan Menteri Keuangan ini mulai berlaku pada tanggal diundangkan. Agar setiap orang mengetahuinya, memerintahkan pengundangan Peraturan Menteri Keuangan ini dengan penempatannya dalam Berita Negara Republik Indonesia.", 10)

c.save()
print(f"PDF dummy dibuat di: {pdf_path}")
