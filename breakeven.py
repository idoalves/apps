import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from datetime import datetime

st.set_page_config(page_title="Simulador de Breakeven", layout="wide")

st.title("Simulador de Breakeven Financeiro")
st.write("Ajuste os parâmetros para simular diferentes cenários de breakeven.")

# Criando colunas para organizar os sliders
col1, col2 = st.columns(2)

with col1:
    st.subheader("Parâmetros Gerais")
    base_revenue = st.slider("Receita Base (mi)", 300, 500, 400, 10)
    base_cost = st.slider("Custos Base (mi)", 500, 700, 600, 10)
    initial_increment = st.slider("Incremento Inicial (mi)", 50, 150, 80, 5)
    growth_rate = st.slider("Taxa de Crescimento Anual", 0.0, 0.5, 0.20, 0.05)
    contract_revenue = st.slider("Receita por Contrato (mi)", 0.5, 3.0, 1.2, 0.1)
    contract_duration = st.slider("Duração do Contrato (anos)", 3, 7, 5, 1)
    renewal_rate = st.slider("Taxa de Renovação", 0.5, 1.0, 0.90, 0.05)
    simulation_horizon = st.slider("Horizonte de Simulação (anos)", 5, 15, 9, 1)

with col2:
    st.subheader("Parâmetros dos Produtos")
    
    st.markdown("**Produto 1**")
    produto1_alocacao = st.slider("Alocação P1 (%)", 0.0, 1.0, 1.0, 0.05)
    produto1_margem_ebitda = st.slider("Margem EBITDA P1 (%)", 0.05, 0.5, 0.30, 0.05)
    produto1_payback = st.slider("Payback P1 (anos)", 0.5, 3.0, 1.5, 0.5)
    produto1_cost_direct = st.slider("Custo Direto P1 (%)", 0.1, 0.8, 0.35, 0.05)
    
    st.markdown("**Produto 2**")
    st.write(f"Alocação P2: {(1 - produto1_alocacao):.2f}")
    produto2_margem_ebitda = st.slider("Margem EBITDA P2 (%)", 0.01, 0.3, 0.10, 0.05)
    produto2_payback = st.slider("Payback P2 (anos)", 0.25, 2.0, 0.5, 0.25)
    produto2_cost_direct = st.slider("Custo Direto P2 (%)", 0.5, 1.0, 0.90, 0.05)

# Botão para executar a simulação
if st.button('Executar Simulação'):
    with st.spinner('Calculando resultados...'):
        produto2_alocacao = 1 - produto1_alocacao
        T = simulation_horizon
        N = T
        
        # Matrizes para Produto 1 e Produto 2
        rev_matrix_p1 = np.zeros((N, T))
        cost_matrix_p1 = np.zeros((N, T))
        rev_matrix_p2 = np.zeros((N, T))
        cost_matrix_p2 = np.zeros((N, T))
        active_contracts_p1 = np.zeros((N, T))
        active_contracts_p2 = np.zeros((N, T))

        def process_cohort(alocacao, margem_ebitda, payback, cost_direct, product_name):
            rev_matrix = np.zeros((N, T))
            cost_matrix = np.zeros((N, T))
            active_contracts = np.zeros((N, T))
            
            for i in range(N):
                R_i = initial_increment * (1 + growth_rate)**i * alocacao
                n_contracts = R_i / contract_revenue
                
                for t in range(i, T):
                    j = t - i
                    cycle = j // contract_duration
                    n_active = n_contracts * (renewal_rate ** cycle)
                    
                    receita = n_active * contract_revenue
                    
                    # Cálculo do investimento
                    if j < int(payback):
                        invest_anual = receita * margem_ebitda
                    elif j == int(payback) and (payback % 1 != 0):
                        invest_anual = receita * margem_ebitda * (payback - int(payback))
                    else:
                        invest_anual = 0
                    
                    # Custos = Investimento + Custo Direto
                    custo_total = invest_anual + (receita * cost_direct)
                    
                    rev_matrix[i, t] = receita
                    cost_matrix[i, t] = custo_total
                    active_contracts[i, t] = n_active
            
            return rev_matrix, cost_matrix, active_contracts
        
        # Processar Produto 1 e Produto 2
        rev_matrix_p1, cost_matrix_p1, active_contracts_p1 = process_cohort(
            produto1_alocacao, produto1_margem_ebitda, produto1_payback, produto1_cost_direct, "Produto 1"
        )
        rev_matrix_p2, cost_matrix_p2, active_contracts_p2 = process_cohort(
            produto2_alocacao, produto2_margem_ebitda, produto2_payback, produto2_cost_direct, "Produto 2"
        )
        
        # Agregar resultados
        yearly_inc_rev = rev_matrix_p1.sum(axis=0) + rev_matrix_p2.sum(axis=0)
        yearly_inc_cost = cost_matrix_p1.sum(axis=0) + cost_matrix_p2.sum(axis=0)
        total_rev = base_revenue + yearly_inc_rev
        total_cost = base_cost + yearly_inc_cost
        contracts_active_p1 = active_contracts_p1.sum(axis=0)
        contracts_active_p2 = active_contracts_p2.sum(axis=0)
        
        # Calcular breakeven
        breakeven_year = next((t for t in range(T) if total_rev[t] >= total_cost[t]), None)
        
        # Plotagem
        fig, ax = plt.subplots(2, 1, figsize=(12, 10))
        
        # Gráfico de Receita vs Custos
        ax[0].plot(range(1, T+1), total_rev, marker='o', label="Receita Total", linewidth=2.5, color='#2E86C1')
        ax[0].plot(range(1, T+1), total_cost, marker='s', label="Custos Totais", linewidth=2.5, color='#E74C3C')
        
        # Área entre as curvas
        ax[0].fill_between(range(1, T+1), total_rev, total_cost, where=(total_rev > total_cost), 
                         color='#ABEBC6', alpha=0.5, label='Lucro')
        ax[0].fill_between(range(1, T+1), total_rev, total_cost, where=(total_rev <= total_cost), 
                         color='#FADBD8', alpha=0.5, label='Prejuízo')
        
        if breakeven_year is not None:
            ax[0].axvline(breakeven_year+1, color='#17A589', linestyle='--', linewidth=2, 
                        label=f'Breakeven: Ano {breakeven_year+1}')
        
        ax[0].set_title("Análise de Breakeven: Receita vs Custos", fontsize=14, fontweight='bold')
        ax[0].grid(True, linestyle='--', alpha=0.7)
        ax[0].legend(fontsize=12)
        ax[0].set_xlabel('Ano', fontsize=12)
        ax[0].set_ylabel('Valores (em milhões)', fontsize=12)
        ax[0].set_xticks(range(1, T+1))
        
        # Gráfico de Contratos Ativos
        ax[1].plot(range(1, T+1), contracts_active_p1, marker='^', color='#3498DB', linewidth=2, 
                 label="Contratos P1")
        ax[1].plot(range(1, T+1), contracts_active_p2, marker='s', color='#9B59B6', linewidth=2, 
                 label="Contratos P2")
        ax[1].plot(range(1, T+1), contracts_active_p1 + contracts_active_p2, marker='d', color='#2ECC71', 
                 linewidth=2.5, label="Total Contratos")
        
        ax[1].set_title("Contratos Ativos por Ano", fontsize=14, fontweight='bold')
        ax[1].grid(True, linestyle='--', alpha=0.7)
        ax[1].legend(fontsize=12)
        ax[1].set_xlabel('Ano', fontsize=12)
        ax[1].set_ylabel('Número de Contratos', fontsize=12)
        ax[1].set_xticks(range(1, T+1))
        
        plt.tight_layout()
        
        # Exibir os gráficos
        st.pyplot(fig)
        
        # Criação da tabela estilizada com pandas
        if breakeven_year is not None:
            st.subheader("Evolução Anual até o Breakeven")
            
            anos = list(range(1, breakeven_year + 2))
            dados = {
                'Ano': anos,
                'Receita Base': [base_revenue] * len(anos),
                'Receita Incremental': yearly_inc_rev[:len(anos)],
                'Receita Total': total_rev[:len(anos)],
                'Despesa Base': [base_cost] * len(anos),
                'Despesa Incremental': yearly_inc_cost[:len(anos)],
                'Despesa Total': total_cost[:len(anos)],
                'Contratos P1': contracts_active_p1[:len(anos)],
                'Contratos P2': contracts_active_p2[:len(anos)],
                'Contratos Totais': (contracts_active_p1 + contracts_active_p2)[:len(anos)]
            }
            
            df = pd.DataFrame(dados)
            
            # Formatação para apresentação
            df_display = df.copy()
            
            # Formatação dos números
            for col in df_display.columns:
                if col == 'Ano':
                    continue
                elif 'Contratos' in col:
                    df_display[col] = df_display[col].apply(lambda x: f"{x:.0f}")
                else:
                    df_display[col] = df_display[col].apply(lambda x: f"{x:.1f} mi")
            
            # Destacar a linha de breakeven
            def highlight_breakeven(x):
                color = 'background-color: #D5F5E3' if x.name == breakeven_year else ''
                return [color for _ in range(len(x))]
            
            # Estilizar e mostrar a tabela
            st.dataframe(df_display.style.apply(highlight_breakeven, axis=1))
            
            # Resumo Final
            st.subheader("Resumo Final")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Breakeven", f"Ano {breakeven_year+1}")
                st.metric("Receita Total no Breakeven", f"{total_rev[breakeven_year]:.1f} mi")
                st.metric("Custos Totais no Breakeven", f"{total_cost[breakeven_year]:.1f} mi")
                st.metric("Margem no Breakeven", f"{(total_rev[breakeven_year] - total_cost[breakeven_year]):.1f} mi")
            
            with col2:
                st.metric("Contratos Ativos - Produto 1", f"{contracts_active_p1[breakeven_year]:.0f}")
                st.metric("Contratos Ativos - Produto 2", f"{contracts_active_p2[breakeven_year]:.0f}")
                st.metric("Contratos Ativos - Total", 
                        f"{(contracts_active_p1[breakeven_year] + contracts_active_p2[breakeven_year]):.0f}")
        else:
            st.warning("Breakeven não alcançado no período simulado.")

st.markdown("---")
st.markdown(f"""
    📝 **Desenvolvido por**: Ido Alves
    • © {datetime.now().year} Todos os direitos reservados
""", unsafe_allow_html=True)
