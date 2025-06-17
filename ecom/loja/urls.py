from django.urls import path, include


from .views import  (
    
    minha_conta_view,
    register_view,
    checkout,
    pedido_sucesso,
    remover_do_carrinho,
    atualizar_quantidade_carrinho,
    IndexView,
    carrinho_detalhe,
    adicionar_ao_carrinho,
    AdicionarAoCarrinhoForm,
    CategoriaListView,
    ProdutoListView,
    ProdutoDetailView,
    CategoriaProdutoListView,
    
)

urlpatterns = [
    path ('', IndexView, name='index'), #Página inicial
    
    path ('produtoslista/', ProdutoListView.as_view(), name='produto_list'), #Lista de produtos
    path ('produtos/<slug:slug>/', ProdutoDetailView.as_view(), name='produto_detalhe'), #Pag. de detalhamento do produto
    path ('categorias/<slug:slug>/', CategoriaProdutoListView.as_view(), name='produtos_por_categoria'), #Produtos por categoria
    path('categorias/', CategoriaListView.as_view(), name='lista_categorias'), #Lista de categorias
   
    path ('carrinho/adicionar/', adicionar_ao_carrinho, name='adicionar_ao_carrinho'), #Adicionar produto ao carrinho
    path ('carrinho/', carrinho_detalhe, name='carrinho_detalhe'), #Detalhe do carrinho

    path('carrinho/atualizar/', atualizar_quantidade_carrinho, name='atualizar_quantidade_carrinho'), # Atualizar quantidade
    path('carrinho/remover/<str:produto_id>/', remover_do_carrinho, name='remover_do_carrinho'), # Remover item

    path('checkout/', checkout, name='checkout'),
    path('pedido/sucesso/<int:pedido_id>/', pedido_sucesso, name='pedido_sucesso'),
    

    path('contas/', include('django.contrib.auth.urls')),
    path('contas/registrar/', register_view, name='register'),
    path('contas/minha-conta/', minha_conta_view, name='minha_conta')
    
]   