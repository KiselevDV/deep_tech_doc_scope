from django.db import models


class Document(models.Model):
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    original_filename = models.CharField(max_length=255)

    def __str__(self):
        return self.original_filename


class Page(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='pages')
    number = models.PositiveIntegerField()
    is_scanned = models.BooleanField(default=False)
    raw_text = models.TextField(blank=True)       # текст, если он есть в PDF
    ocr_text = models.TextField(blank=True)       # текст, полученный из OCR
    classification = models.CharField(
        max_length=100, blank=True, null=True,
        help_text='Тип содержимого страницы: сертификат, титульный лист и т.п.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    width = models.FloatField(null=True)
    height = models.FloatField(null=True)

    class Meta:
        unique_together = ('document', 'number')


class TextBlock(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='blocks')
    x0 = models.FloatField()
    y0 = models.FloatField()
    x1 = models.FloatField()
    y1 = models.FloatField()
    text = models.TextField()


class Material(models.Model):
    page = models.ForeignKey(Page, related_name='materials', on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    characteristics = models.JSONField(default=dict)  # например, {"ГОСТ": "1234-56", "Марка": "12Х18Н10Т"}

    def __str__(self):
        return f"{self.name} ({self.page})"
