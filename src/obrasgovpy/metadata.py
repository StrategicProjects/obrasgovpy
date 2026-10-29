"""The resources, their filters and the enumerated values.

This mirrors the OpenAPI contract published at
``https://api-publica.obrasgov.gestao.gov.br/obras/openapi.json`` and the R
sibling package `obrasgovr`. Filter names and categorical values are in
Portuguese because they belong to the API.
"""

from __future__ import annotations

import pandas as pd

RESOURCES = {
    "projects": {
        "endpoint": "projeto-investimento",
        "function": "get_projects",
        "filters": {
            "id_projeto_investimento": "str",
            "projeto_estruturante": "str",
            "desc_nome": "str",
            "nr_cep": "str",
            "desc_endereco": "str",
            "desc_projeto": "str",
            "desc_funcao_social": "str",
            "desc_meta_global": "str",
            "dt_inicial_prevista": "date",
            "dt_final_prevista": "date",
            "dt_cadastro": "date",
            "ano_cadastro": "int",
            "natureza_intervencao": "str",
            "id_natureza_intervencao": "int",
            "especie_intervencao": "str",
            "id_especie_intervencao": "int",
            "situacao": "str",
            "uf_principal": "str",
            "organizacao_resp": "str",
            "cnpj_organizacao_resp": "str",
            "populacao_beneficiada": "int",
            "desc_populacao_beneficiada": "str",
            "qtd_empregos_gerados": "int",
            "ind_bim": "int",
            "dt_inicial_efetiva": "date",
            "dt_final_efetiva": "date",
            "obs_pertinentes_intervencao": "str",
            "sistema_resp": "str",
            "possui_estudo_viabilidade": "str",
        },
    },
    "commitments": {
        "endpoint": "empenho",
        "function": "get_commitments",
        "filters": {
            "ug_emitente": "int",
            "id_projeto_investimento": "str",
            "programa_trabalho": "str",
            "plano_interno": "str",
            "fonte": "str",
            "natureza_despesa": "int",
            "valor_empenho": "float",
            "sistema_origem_empenho": "str",
            "bd_origem_empenho": "str",
            "id_minuta": "str",
            "organizacao_empenho": "str",
            "data_emissao": "date",
            "nome_situacao_minuta": "str",
            "unidade_orcamentaria": "str",
            "programa_trabalho_resumido": "str",
            "resultado_primario": "str",
            "acao_orcamentaria": "str",
            "codigo_autor_emenda": "str",
            "nr_empenho": "str",
            "credor": "str",
            "aliquidar": "float",
            "liquidado": "float",
            "pago": "float",
            "rpinscrito": "float",
            "rpaliquidar": "float",
            "rpaliquidado": "float",
            "rppago": "float",
            "descricao_empenho": "str",
        },
    },
    "physical_execution": {
        "endpoint": "execucao-fisica",
        "function": "get_physical_execution",
        "filters": {
            "id_projeto_investimento": "str",
            "percentual_execucao_fisica": "float",
            "dt_inicial_execucao": "date",
            "dt_final_execucao": "date",
            "tipo_instrumento": "str",
            "tipo_forma_execucao": "str",
            "dt_criacao_instrumento": "date",
            "dt_cadastro_execucao": "date",
            "dt_atualizacao_execucao": "date",
        },
    },
    "contracts": {
        "endpoint": "contrato",
        "function": "get_contracts",
        "filters": {
            "id_projeto_investimento": "str",
            "id_contrato": "int",
            "numero_contrato": "str",
            "vigencia_inicio_contrato": "date",
            "vigencia_fim_contrato": "date",
            "data_assinatura_contrato": "date",
            "data_publicacao_contrato": "date",
            "modalidade_contrato": "str",
            "objeto_contrato": "str",
            "processo": "str",
            "receita_despesa_contrato": "str",
            "orgao_contrato": "str",
            "cnpj_fornecedor_contrato": "str",
            "fornecedor_contrato": "str",
            "categoria_contrato": "str",
            "licitacao_numero": "str",
            "situacao_contrato": "str",
            "link_transparencia": "str",
            "valor_global_contrato": "float",
            "valor_acumulado_contrato": "float",
            "valor_utilizado_pi_contrato": "float",
            "valor_incluido_contrato": "float",
        },
    },
    "geometries": {
        "endpoint": "geometria",
        "function": "get_geometries",
        "filters": {
            "id_projeto_investimento": "str",
            "id_geometria": "int",
            "sg_uf": "str",
            "no_municipio": "str",
            "cod_ibge": "int",
            "origem_geometria": "str",
        },
    },
    "status_history": {
        "endpoint": "historico-situacao-cancelada-paralisada",
        "function": "get_status_history",
        "filters": {
            "id_historico_situacao_investimento": "int",
            "descricao_historico_situacao_investimento": "str",
            "data_historico_situacao_investimento": "date",
            "justificativa_cancelada_paralisada": "str",
            "possui_tratativas_situacao_investimento": "str",
            "fase_tratativas_situacao_investimento": "str",
            "id_projeto_investimento": "str",
        },
    },
    "feasibility_studies": {
        "endpoint": "estudo-viabilidade",
        "function": "get_feasibility_studies",
        "filters": {
            "id_projeto_investimento": "str",
            "tipo_estudo_viabilidade": "str",
            "especificacao_estudo_viabilidade": "str",
        },
    },
    "last_update": {
        "endpoint": "data-atualizacao",
        "function": "get_last_update",
        "filters": {},
    },
}

_UFS = (
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG",
    "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR",
    "RS", "SC", "SE", "SP", "TO",
)

CHOICES = {
    "projeto_estruturante": ("NÃO", "SIM"),
    "natureza_intervencao": (
        "Outros", "Projeto", "Estudo",
        "Projeto de Investimento em Infraestrutura", "Obra",
    ),
    "especie_intervencao": (
        "Máquinas e Equipamentos", "Recuperação", "Construção", "Reforma",
        "Ampliação", "Fabricação",
    ),
    "situacao": (
        "Cadastrada", "Cancelada", "Concluída", "Em execução", "Inacabada",
        "Paralisada",
    ),
    "uf_principal": _UFS,
    "possui_estudo_viabilidade": ("NÃO", "SIM"),
    "sistema_origem_empenho": ("PMBDISCRICIONARIAS", "CIPI", "COMPRASNET CONTRATOS"),
    "bd_origem_empenho": ("modulo_siafi", "cipiws"),
    "nome_situacao_minuta": ("ENVIADO", "EM ALTERAÇÃO", "PENDENTE"),
    "receita_despesa_contrato": ("Despesa", "Receita"),
    "categoria_contrato": (
        "A definir", "Cessão", "Compras", "Informática (TIC)", "Mão de Obra",
        "Obras", "Serviços", "Serviços de Engenharia",
    ),
    "sg_uf": _UFS,
    "origem_geometria": ("Par de Lat/Long", "Shapefile", "Vetorização"),
    "tipo_estudo_viabilidade": ("Econômica", "Ambiental", "Social", "Técnica", "Outros"),
}

# Resource names the R sibling's Portuguese aliases use.
PORTUGUESE_RESOURCES = {
    "projetos": "projects",
    "empenhos": "commitments",
    "execucao_fisica": "physical_execution",
    "contratos": "contracts",
    "geometrias": "geometries",
    "historico_situacao": "status_history",
    "estudos_viabilidade": "feasibility_studies",
    "data_atualizacao": "last_update",
}


def match_resource(resource: str) -> str:
    if not isinstance(resource, str):
        raise ValueError("resource must be a single string.")

    resource = PORTUGUESE_RESOURCES.get(resource, resource)
    if resource not in RESOURCES:
        choices = ", ".join(RESOURCES)
        raise ValueError(f"Unknown resource: {resource!r}. Choose one of: {choices}.")
    return resource


def list_resources() -> pd.DataFrame:
    """List the API resources this package covers, one row per resource."""
    return pd.DataFrame(
        {
            "resource": list(RESOURCES),
            "function": [meta["function"] for meta in RESOURCES.values()],
            "endpoint": [meta["endpoint"] for meta in RESOURCES.values()],
            "paginated": [name != "last_update" for name in RESOURCES],
        }
    )


def list_filters(resource: str) -> pd.DataFrame:
    """List the filters a resource accepts, with their types and enum values.

    Unknown filters are rejected before a request is sent, to prevent silently
    incorrect queries. Filter names and categorical values remain in Portuguese
    because they are part of the upstream API contract.
    """
    resource = match_resource(resource)
    filters = RESOURCES[resource]["filters"]

    return pd.DataFrame(
        {
            "filter": list(filters),
            "type": list(filters.values()),
            "allowed_values": [list(CHOICES.get(name, ())) for name in filters],
        }
    )


def date_fields(resource: str) -> list[str]:
    """The filters a resource declares as dates."""
    filters = RESOURCES[match_resource(resource)]["filters"]
    return [name for name, kind in filters.items() if kind == "date"]
