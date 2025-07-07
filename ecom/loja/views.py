from django.views.generic import ListView, DetailView
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django import forms
from django.db import transaction
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal
from .forms import ConfirmacaoPedidoForm, CustomUserCreationForm, ClienteProfileForm, UserEditForm, ClienteProfileEditForm
from .models import Produto, Categoria, Cliente, Pedido, ItemPedido



#------------------Página inicial--------------

def IndexView(request):
    return render(request, 'index.html', {}) 
#------------------Categorias------------------
class CategoriaProdutoListView(ListView):
    template_name = 'produtos_por_categoria.html'
    context_object_name = 'produtos'

    def get_queryset(self):
        self.categoria = get_object_or_404(Categoria, slug=self.kwargs['slug']) 
        return Produto.objects.filter(categoria=self.categoria)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categoria'] = self.categoria
        return context
    
class CategoriaListView(ListView):
    model = Categoria
    template_name = 'categoria_list.html'
    context_object_name = 'categorias'
    ordering = ['nome']

    def get_queryset(self):
        return Categoria.objects.all()
    


#--------------- Produtos ---------------------

class ProdutoListView(ListView):
    model = Produto
    template_name = 'produto_list.html'
    context_object_name = 'produtos'
    
class ProdutoDetailView(DetailView):
    model = Produto
    template_name = 'produto_detalhe.html'
    context_object_name = 'produto'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'


    #------------------ Cadastro de cliente ---------------------

def register_view(request):
        if request.method == 'POST':
            user_form = CustomUserCreationForm(request.POST)
            profile_form = ClienteProfileForm(request.POST)

            if user_form.is_valid() and profile_form.is_valid():

                user = user_form.save()
                cliente_profile = profile_form.save(commit=False)
                cliente_profile.user = user
                cliente_profile.save()

                login(request, user) 

                messages.success(request, f'Conta criada com sucesso! Bem-vindo(a), {user.username}!')

                return redirect('index')  
            else:
                messages.error(request, 'Erro, Verifique os dados abaixo e tente novamente.')
        else:
            user_form = CustomUserCreationForm()
            profile_form = ClienteProfileForm()
        
        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'page_title': 'Criar nova conta',
        }
        return render(request, 'registro_clientes/registro.html', context)

#------------------ Minha conta ---------------------
@login_required
def minha_conta_view(request):
    try:
        cliente = request.user.cliente
    except Cliente.DoesNotExist:
        return redirect('home')
    
    status_em_andamento= ['aguardando', 'processando', 'enviado']
    status_anteriores = ['entregue', 'cancelado']

    pedidos_em_andamento = Pedido.objects.filter(
        cliente=cliente,
        status__in=status_em_andamento
    ).order_by('-data_pedido')

    pedidos_anteriores = Pedido.objects.filter(
        cliente=cliente,
        status__in=status_anteriores
    ).order_by('-data_pedido')

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ClienteProfileEditForm(request.POST, request.FILES, instance=cliente)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Alterações salvas com sucesso!')
            return redirect('minha_conta')
    else:
            user_form = UserEditForm(instance=request.user)
            profile_form = ClienteProfileEditForm(instance=cliente)

    context = {
        'user_form' : user_form,
        'profile_form' : profile_form,
        'pedidos_em_andamento': pedidos_em_andamento,
        'pedidos_anteriores': pedidos_anteriores,
        'cliente' : cliente
    }
    return render(request, 'registration/minha_conta.html', context)

#------------------Detalhe de visualização do pedido---------------------

class PedidoDetailView(LoginRequiredMixin, DetailView):
    model = Pedido
    template_name = 'pedido_detalhe.html'
    context_object_name = 'pedido'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        queryset = super().get_queryset()

        return queryset.filter(cliente__user=self.request.user)
    
#------------------------Histórico de pedidos do cliente------------------------

class PedidoListView(LoginRequiredMixin, ListView):
    model = Pedido
    template_name = 'pedido_list.html'
    context_object_name = 'pedidos'
    paginate_by = 10

    def get_queryset(self):
        
        if hasattr(self.request.user, 'cliente'):
            return Pedido.objects.filter(cliente=self.request.user.cliente).order_by('-data_pedido')
        return Pedido.objects.none()

#------------------ Pedidos do cliente logado---------------------

@login_required
@transaction.atomic

def checkout (request):
    carrinho_sessao = request.session.get('carrinho', {})
    if not carrinho_sessao:
        messages.warning(request, 'Seu carrinho está vazio.')
        return redirect('carrinho_detalhe')
    
    try:
        cliente = request.user.cliente
    except Cliente.DoesNotExist:
        #FUTURAMENTE SERÁ FEITA A PÁGINA DE CADASTRO DO CLIENTE
        #TERA UM REDIRECIONAMENTO PARA A PÁGINA DE CADASTRO
        messages.error(request, 'Você precisa ser um cliente cadastrado para fazer um pedido.')
        #return redirect('cadastro_cliente')  # Redirecionar para a página de cadastro do cliente
    total_carrinho = Decimal('0.00')
    carrinho_para_template = {}
    for produto_id_str, item_data in carrinho_sessao.items():
        item_display_data = item_data.copy() # Copia os dados do item
        try: 
            preco = Decimal(item_data.get('preco', '0.00'))
            quantidade = item_data.get('quantidade', 0)
            subtotal_item = preco * quantidade
            item_display_data['subtotal'] = subtotal_item
            total_carrinho += subtotal_item
        except (TypeError, ValueError) as e: 
          messages.error(request, f"Erro ao processar o item {item_data.get('nome', produto_id_str)} no carrinho {e}")
          return redirect('carrinho_detalhe')
        carrinho_para_template[produto_id_str] = item_display_data

        #FORMULÁRIO DO CARAIO DO CARRINHO QUE BATI CABEÇA PRA UM INFERNO PORRA

    if request.method == 'POST':
        form = ConfirmacaoPedidoForm(request.POST)
        if form.is_valid():
           #objeto pedido
           pedido = Pedido.objects.create(cliente=cliente)

           for produto_id_str, item_data_sessao in carrinho_sessao.items():
               prduto_id_int = int(produto_id_str)
               quantidade_pedida = item_data_sessao['quantidade']

               try: 
                   produto = Produto.objects.select_for_update().get(id=prduto_id_int)
               except Produto.DoesNotExist:
                   messages.error(request, f"O produto '{item_data_sessao['nome']}'não esta mais disponível. Pedido não finalizado")
                   return redirect('carrinho_detalhe')
               
               if produto.estoque < quantidade_pedida:
                messages.error(request, f"Estoque insuficiente para o produto '{produto.nome}'. Disponível: {produto.estoque}.")
                return redirect('carrinho_detalhe')
               
               ItemPedido.objects.create(
                   pedido=pedido,
                   produto=produto,
                   quantidade= quantidade_pedida,
                   preco_unitario=produto.preco
                )
               produto.estoque  -= quantidade_pedida
               produto.save()

               del request.session['carrinho']  # clear np carrinho após o pedido
               request.session.modified = True
               messages.success(request, f"Pedido #{pedido.id} realizado com sucesso!")
               return redirect('pedido_sucesso', pedido_id=pedido.id)
    else:
            form = ConfirmacaoPedidoForm()

    context = {
            'form' : form,
            'carrinho_itens' : carrinho_para_template,
            'total_carrinho' : total_carrinho,
            'cliente' : cliente,
        }

    return render (request, 'checkout.html', context)

@login_required
def pedido_sucesso(request,pedido_id):
    try:
        pedido = Pedido.objects.get(id=pedido_id, cliente__user=request.user)
    except Pedido.DoesNotExist:
        messages.error(request, "Pedido não encontrado.")
        return redirect('lista_pedidos')
    
    context = {
        'pedido': pedido,

    }
    return render(request, 'pedido_sucesso.html', context)    


         #------------------ Carrinho de compras ---------------------

class AdicionarAoCarrinhoForm(forms.Form):
    quantidade = forms.IntegerField(min_value=1)
    produto_id = forms.IntegerField(widget=forms.HiddenInput())

def adicionar_ao_carrinho(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    carrinho = request.session.get('carrinho', {})
    produto_id_str = str(produto_id)

    # --- INÍCIO DA ATUALIZAÇÃO ---
    # Pega a quantidade do formulário. Se não for enviada, assume 1.
    quantidade_a_adicionar = int(request.POST.get('quantidade', 1))
    # --- FIM DA ATUALIZAÇÃO ---

    # Verifica o estoque
    quantidade_atual_carrinho = carrinho.get(produto_id_str, {}).get('quantidade', 0)
    estoque_necessario = quantidade_atual_carrinho + quantidade_a_adicionar

    if produto.estoque < estoque_necessario:
        messages.error(request, f"Estoque insuficiente para a quantidade desejada de '{produto.nome}'.")
        return redirect('produto_detalhe', slug=produto.slug)

    # Adiciona ou atualiza o produto no carrinho
    if produto_id_str in carrinho:
        carrinho[produto_id_str]['quantidade'] += quantidade_a_adicionar
    else:
        carrinho[produto_id_str] = {
            'quantidade': quantidade_a_adicionar,
            'preco': str(produto.preco),
            'nome': produto.nome,
            'imagem_url': produto.imagem.url if produto.imagem else '',
            'slug': produto.slug
        }

    request.session['carrinho'] = carrinho
    request.session.modified = True
    
    messages.success(request, f'{quantidade_a_adicionar}x "{produto.nome}" foi(ram) adicionado(s) ao seu carrinho.')
    return redirect('carrinho_detalhe')  
    

def carrinho_detalhe(request):
    carrinho = request.session.get('carrinho', {}) 
    total_carrinho = Decimal('0.00')

    for produto_id, item in carrinho.items():
        try:
            preco = Decimal(item.get('preco', '0.00'))
            quantidade = item.get('quantidade', 0)
            
            subtotal = preco * quantidade
            item['subtotal'] = subtotal 
            
            total_carrinho += subtotal

            try:
                produto_obj = Produto.objects.get(id=int(produto_id))
                item['produto_obj'] = produto_obj
            except Produto.DoesNotExist:
                item['produto_obj'] = None
        
        except (KeyError, TypeError, ValueError):
            print(f"Erro ao calcular item no carrinho: {item}") 
            pass  
    
    return render(request, 'carrinho_detalhe.html', {
        'carrinho': carrinho,
        'total_carrinho': total_carrinho,
    })

def atualizar_quantidade_carrinho(request, produto_id, nova_quantidade):
    carrinho = request.session.get('carrinho', {})
    produto_id_str = str(produto_id)

    if request.method == 'POST':
        try:
            produto = Produto.objects.get(id=produto_id_str)
            quantidade = int(nova_quantidade)

            if quantidade > 0 and produto.estoque >= quantidade:
                carrinho[produto_id_str]['quantidade'] = quantidade
                request.session['carrinho'] = carrinho
                request.session.modified = True
                
                # Recalcula os totais para enviar de volta ao frontend
                item_subtotal = produto.preco * quantidade
                
                total_carrinho = Decimal('0.00')
                for pid, item in carrinho.items():
                    prod = Produto.objects.get(id=pid)
                    total_carrinho += prod.preco * item['quantidade']
                
                return JsonResponse({
                    'success': True, 
                    'item_subtotal': f'{item_subtotal:.2f}',
                    'cart_total': f'{total_carrinho:.2f}'
                })
            else:
                 return JsonResponse({'success': False, 'error': 'Quantidade inválida ou estoque insuficiente.'})

        except (Produto.DoesNotExist, ValueError):
            return JsonResponse({'success': False, 'error': 'Produto ou quantidade inválidos.'})
    
    return JsonResponse({'success': False, 'error': 'Requisição inválida.'})


def remover_do_carrinho(request, produto_id):
    carrinho = request.session.get('carrinho', {})
    produto_id_str = str(produto_id)

    if request.method == 'POST' and produto_id_str in carrinho:
        del carrinho[produto_id_str]
        request.session['carrinho'] = carrinho
        request.session.modified = True

        # Recalcula o total do carrinho
        total_carrinho = Decimal('0.00')
        for pid, item in carrinho.items():
            try:
                prod = Produto.objects.get(id=pid)
                total_carrinho += prod.preco * item['quantidade']
            except Produto.DoesNotExist:
                continue

        return JsonResponse({'success': True, 'cart_total': f'{total_carrinho:.2f}'})

    return JsonResponse({'success': False, 'error': 'Não foi possível remover o item.'})

#------------------ Pesquisa de produtos ---------------------
def pesquisa_view(request): 
    query = request.GET.get('q', '').strip()
    resultados = []
    if query:
        resultados = Produto.objects.filter(
            Q(nome__icontains=query) | Q(descricao__icontains=query)
        ).distinc()
        
        context = {
            'query' : query,
            'resultados' : resultados,
        }
        return render (request, 'loja/pesquisa.html', context)
    
def produto_api_list(request):
    produtos = Produto.objects.filter(disponivel=True).order_by('nome')
    data = []

    for produto in produtos:
        try:
            
            imagem_url = ''
            if produto.imagem:
                imagem_url = request.build_absolute_uri(produto.imagem.url)

            
            produto_url = request.build_absolute_uri(produto.get_absolute_url())

            
            item = {
                'nome': produto.nome,
                'url': produto_url,
                'imagem_url': imagem_url
            }
            data.append(item)

        except Exception as e:
            
            print(f"Erro ao processar o produto '{produto.nome}' para a API: {e}")
            continue
        
    return JsonResponse(data, safe=False) 


    


        