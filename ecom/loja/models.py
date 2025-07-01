from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User

# Create your models here.

class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    descricao = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

class Produto(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100, unique=True)
    slug =models.SlugField(max_length=120, unique=True, blank=True)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    estoque = models.PositiveIntegerField(default=0)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name= 'produtos')
    imagem = models.ImageField(upload_to='produtos/', blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta: 
        ordering = ['nome']
      
    def save (self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome
    
class Cliente(models.Model):
    TIPO_PESSOA_FISICA = 'PF'
    TIPO_PESSOA_JURIDICA = 'PJ'
    TIPO_CLIENTE_CHOICES = [
        (TIPO_PESSOA_FISICA, 'Pessoa Física'),
        (TIPO_PESSOA_JURIDICA, 'Pessoa Jurídica'),
    ]
    # Campo comum
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo_cliente = models.CharField(max_length=2, choices=TIPO_CLIENTE_CHOICES, default=TIPO_PESSOA_FISICA)
    telefone = models.CharField(max_length=20)
    endereco = models.TextField(help_text='Endereço completo do cliente')

    #campo pessoa física
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True, help_text="Formato: 123.456.789-00")

    #campo pessoa jurídica
    razao_social = models.CharField(max_length=255, null=True, blank=True)
    nome_fantasia = models.CharField(max_length=255, null=True, blank=True)
    cnpj = models.CharField(max_length=18, unique=True, null=True, blank=True, help_text="Formato: 12.345.678/0001-99")
    inscricao_estadual = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        if self.tipo_cliente == self.TIPO_PESSOA_JURIDICA and self.razao_social:
            return self.razao_social
        return self.user.get_full_name() or self.user.username
    
    def save(self, *args, **kwargs):
        
        if self.tipo_cliente == self.TIPO_PESSOA_FISICA:
            self.razao_social = None
            self.nome_fantasia = None
            self.cnpj = None
            self.inscricao_estadual = None
        elif self.tipo_cliente == self.TIPO_PESSOA_JURIDICA:
            self.cpf = None
        super().save(*args, **kwargs)

    

class Pedido(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    data_pedido = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = [
        ('aguardando', 'Aguardando Pagamento'),
        ('processando', 'Processando'),
        ('enviado', 'Enviado'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aguardando')
    codigo_rastreamento = models.CharField(max_length=100, blank=True , null=True)

    def __str__(self):
        return f"Pedido {self.id} - {self.cliente.user.username}"
    
    @property
    def total(self):
        return sum(item.subtotal for item in self.itens.all())
    
    
class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantidade} x {self.produto.nome} (Pedido {self.pedido.id})"
    
    @property
    def subtotal(self):
        return self.quantidade * self.preco_unitario

    

