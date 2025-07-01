from django.contrib import admin
from .models import Categoria, Produto, Cliente, Pedido, ItemPedido

# Register your models here.


#---------------------Categoria -------------------
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome','slug','criado_em', 'atualizado_em')
    prepopulated_fields = {'slug': ('nome',)}
    search_fields = ['nome']
    ordering = ['nome']


#---------------------Produto----------------------
@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'preco', 'estoque', 'categoria', 'criado_em',)
    search_fields = ('nome', 'categoria__nome')
    list_filter = ('categoria', 'criado_em')
    prepopulated_fields = {'slug': ('nome',)}
    ordering = ('nome',)



#---------------------Cliente---------------------
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('user', 'telefone', 'endereco')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    oerdering = ('user__username',)


#---------------------ItemPedido(inline)---------------
class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1 #sem linhas vazias a serem adicionados
    readonly_fields = ['subtotal'] #campo somente leitura
    raw_id_fields = ['produto'] #campo que pode ser editado diretamente

#--------------------------Pedido----------------------
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'data_pedido', 'status', 'codigo_rastreamento']
    list_filter = ['status', 'data_pedido']
    search_fields = ['id', 'cliente__user__username', 'cliente__razao_social', 'codigo_rastreamento']
    ordering = ['-data_pedido']
    inlines = [ItemPedidoInline]
    
    readonly_fields = ('cliente', 'data_pedido', 'total')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related('itens__produto', 'cliente__user')
        return queryset
    