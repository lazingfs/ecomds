from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Cliente 

#-----------------------coNFIRMAÇÃO DO PEDIDO-----------------------
class ConfirmacaoPedidoForm(forms.Form):
    
 pass 


#-----------------------FORMULÁRIOS DE USUÁRIO-----------------------
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Obrigatório. Informe um endereçõ válido")
    primeiro_nome = forms.CharField(max_length=30, required=False , help_text="Opcional.")
    ultimo_nome = forms.CharField(max_length=30, required=False, help_text="Opcional.")

    class Meta(UserCreationForm.Meta):
       model = User 
       fields = UserCreationForm.Meta.fields + ('email', 'primeiro_nome', 'ultimo_nome',)

class ClienteProfileForm(forms.ModelForm):
    class Meta:
       model = Cliente 
       fields = [
          'tipo_cliente', 'telefone', 'endereco',
          'cpf',
          'razao_social', 'nome_fantasia', 'cnpj', 'inscricao_estadual'
       ]
       widgets = {
          'tipo_cliente': forms.RadioSelect,
         'endereco' : forms.Textarea(attrs={'rows': 3}),
         }
       
       def clean(self):
         cleaned_data = super().clean()
         tipo_cliente = cleaned_data.get('tipo_cliente')

         if tipo_cliente == Cliente.TIPO_PESSOA_FISICA:

            if not cleaned_data .get('cpf'):
                self.add_error('cpf', 'CPF é obrigatório para Pessoa Física.')


         elif tipo_cliente == Cliente.TIPO_PESSOA_JURIDICA:

            if not cleaned_data.get('razao_social'):
                self.add_error('razao_social', 'Razão Social é obrigatória para Pessoa Jurídica.')
            if not cleaned_data.get('cnpj'):
                  self.add_error('cnpj', 'CNPJ é obrigatório para Pessoa Jurídica.')

         return cleaned_data
       

       #------------------------edição para conta cliente------------------------
class UserEditForm(forms.ModelForm):
   class Meta: 
      model = User
      fields = ['first_name', 'last_name', 'email']
      labels = {
         'first_name': 'Nome',
         'last_name': 'Sobrenome',
         'email': 'E-mail de contato',
      }
      help_texts = { 
         'email': 'Este e-mail será usado para comunicação de recuperação de senha.'
      }

class ClienteProfileEditForm(forms.ModelForm):
   
   class Meta:
      model = Cliente
      
      exclude = ['user', 'tipo_cliente']
      wigets = {
         'telefone': 'Telefone(com DDD)',
         'endereco': 'Endereco Completo(Rua, Número, Bairro, Cidade, CEP)',
         'cpf': 'CPF',
         'razao_social': 'Razao Social',
         'nome_fantasia': 'Nome Fantasia',
         'cnpj': 'CNPJ',
         'inscricao_estadual': 'Inscrição Estadual (se aplicácel)',
      }

   def __init__(self, *args, **kwargs):

      super().__init__(*args, **kwargs)

      instance = getattr(self, 'instance', None)

      if instance and instance.pk:

         if instance.tipo_cliente == Cliente.TIPO_PESSOA_FISICA:

            del self.fields['razao_social']
            del self.fields['nome_fantasia']
            del self.fields['cnpj']
            del self.fields['inscricao_estadual']
         elif instance.tipo_cliente == Cliente.TIPO_PESSOA_JURIDICA:

            del self.fields['cpf']
     