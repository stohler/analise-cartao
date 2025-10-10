#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Parser para XMLs de Nota Fiscal Eletrônica (NFe)
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional
import re
from subtransaction_models import SubTransaction, SubTransactionXML, categorize_supermarket_item

class NFeParser:
    """Parser para XMLs de NFe"""
    
    def __init__(self):
        self.namespaces = {
            'nfe': 'http://www.portalfiscal.inf.br/nfe',
            'ns2': 'http://www.portalfiscal.inf.br/nfe'
        }
    
    def parse_xml_file(self, file_path: str) -> Optional[SubTransactionXML]:
        """Parse um arquivo XML de NFe"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return self.parse_xml_content(root, file_path)
        except Exception as e:
            print(f"Erro ao parsear arquivo XML {file_path}: {e}")
            return None
    
    def parse_xml_content(self, root: ET.Element, filename: str = None) -> Optional[SubTransactionXML]:
        """Parse o conteúdo XML de uma NFe"""
        try:
            # Encontrar o elemento NFe
            nfe = self._find_nfe_element(root)
            if not nfe:
                print("Elemento NFe não encontrado no XML")
                return None
            
            # Extrair informações básicas
            xml_info = self._extract_xml_info(nfe)
            if not xml_info:
                print("Não foi possível extrair informações básicas do XML")
                return None
            
            # Criar objeto XML
            xml_obj = SubTransactionXML(
                xml_id=xml_info['xml_id'],
                filename=filename or 'xml_importado.xml',
                total_value=xml_info['total_value'],
                emission_date=xml_info['emission_date'],
                establishment_name=xml_info['establishment_name']
            )
            
            # Extrair itens
            items = self._extract_items(nfe)
            for item in items:
                subtransaction = SubTransaction(
                    item_id=item['item_id'],
                    description=item['description'],
                    quantity=item['quantity'],
                    unit_value=item['unit_value'],
                    total_value=item['total_value'],
                    category=item['category'],
                    subcategory=item['subcategory']
                )
                xml_obj.add_subtransaction(subtransaction)
            
            return xml_obj
            
        except Exception as e:
            print(f"Erro ao parsear conteúdo XML: {e}")
            return None
    
    def _find_nfe_element(self, root: ET.Element) -> Optional[ET.Element]:
        """Encontra o elemento NFe no XML"""
        # Tentar diferentes caminhos para encontrar a NFe
        paths = [
            './/nfe:NFe',
            './/ns2:NFe', 
            './/NFe',
            './proc/nfe:nfeProc/nfe:NFe',
            './proc/ns2:nfeProc/ns2:NFe',
            './proc/nfeProc/NFe',
            './proc/nfe:nfeProc/NFe',
            './proc/ns2:nfeProc/NFe',
            './/proc/nfe:nfeProc/nfe:NFe',
            './/proc/ns2:nfeProc/ns2:NFe',
            './/proc/nfeProc/NFe',
            './/proc/nfe:nfeProc/NFe',
            './/proc/ns2:nfeProc/NFe'
        ]
        
        for path in paths:
            try:
                element = root.find(path, self.namespaces)
                if element is not None:
                    return element
            except:
                continue
        
        # Se não encontrou com namespaces, tentar sem
        for path in ['.//NFe', './proc/nfeProc/NFe', './proc/NFe', './/proc/nfeProc/NFe', './/proc/NFe']:
            element = root.find(path)
            if element is not None:
                return element
        
        return None
    
    def _extract_xml_info(self, nfe: ET.Element) -> Optional[Dict]:
        """Extrai informações básicas da NFe"""
        try:
            # ID da NFe - procurar diretamente nos filhos do NFe
            infnfe = None
            for child in nfe:
                if 'infNFe' in child.tag:
                    infnfe = child
                    break
            
            xml_id = ''
            if infnfe is not None:
                xml_id = infnfe.get('Id', '')
                if xml_id.startswith('NFe'):
                    xml_id = xml_id[3:]  # Remove prefixo 'NFe'
            
            # Informações do emitente
            emit = None
            if infnfe is not None:
                for child in infnfe:
                    if 'emit' in child.tag:
                        emit = child
                        break
            
            establishment_name = 'Estabelecimento não identificado'
            if emit is not None:
                xfant = None
                xnome = None
                for child in emit:
                    if 'xFant' in child.tag:
                        xfant = child
                    elif 'xNome' in child.tag:
                        xnome = child
                
                establishment_name = (xfant.text if xfant is not None and xfant.text 
                                    else xnome.text if xnome is not None and xnome.text 
                                    else 'Estabelecimento não identificado')
            
            # Data de emissão
            ide = None
            if infnfe is not None:
                for child in infnfe:
                    if 'ide' in child.tag:
                        ide = child
                        break
            
            emission_date = datetime.now()
            if ide is not None:
                dhemi = None
                for child in ide:
                    if 'dhEmi' in child.tag:
                        dhemi = child
                        break
                
                if dhemi is not None and dhemi.text:
                    try:
                        # Formato: 2025-09-23T18:28:05-03:00
                        emission_date = datetime.fromisoformat(dhemi.text.replace('Z', '+00:00'))
                    except:
                        pass
            
            # Valor total
            total = None
            if infnfe is not None:
                for child in infnfe:
                    if 'total' in child.tag:
                        total = child
                        break
            
            total_value = 0.0
            if total is not None:
                icmstot = None
                for child in total:
                    if 'ICMSTot' in child.tag:
                        icmstot = child
                        break
                
                if icmstot is not None:
                    vnf = None
                    for child in icmstot:
                        if 'vNF' in child.tag:
                            vnf = child
                            break
                    
                    if vnf is not None and vnf.text:
                        try:
                            total_value = float(vnf.text)
                        except:
                            pass
            
            return {
                'xml_id': xml_id,
                'total_value': total_value,
                'emission_date': emission_date,
                'establishment_name': establishment_name
            }
            
        except Exception as e:
            print(f"Erro ao extrair informações básicas: {e}")
            return None
    
    def _extract_items(self, nfe: ET.Element) -> List[Dict]:
        """Extrai itens da NFe"""
        items = []
        
        # Encontrar o elemento infNFe primeiro
        infnfe = None
        for child in nfe:
            if 'infNFe' in child.tag:
                infnfe = child
                break
        
        if infnfe is None:
            return items
        
        # Encontrar todos os elementos det (detalhes dos produtos)
        det_elements = []
        for child in infnfe:
            if 'det' in child.tag:
                det_elements.append(child)
        
        for det in det_elements:
            try:
                item_info = self._extract_item_info(det)
                if item_info:
                    items.append(item_info)
            except Exception as e:
                print(f"Erro ao extrair item: {e}")
                continue
        
        return items
    
    def _extract_item_info(self, det: ET.Element) -> Optional[Dict]:
        """Extrai informações de um item específico"""
        try:
            # Número do item
            nitem = det.get('nItem', '1')
            item_id = f"item_{nitem}"
            
            # Informações do produto
            prod = None
            for child in det:
                if 'prod' in child.tag:
                    prod = child
                    break
            
            if prod is None:
                return None
            
            # Descrição do produto
            xprod = None
            for child in prod:
                if 'xProd' in child.tag:
                    xprod = child
                    break
            description = xprod.text if xprod is not None and xprod.text else 'Produto não identificado'
            
            # Quantidade
            qcom = None
            for child in prod:
                if 'qCom' in child.tag:
                    qcom = child
                    break
            quantity = 1.0
            if qcom is not None and qcom.text:
                try:
                    quantity = float(qcom.text)
                except:
                    pass
            
            # Valor unitário
            vuncom = None
            for child in prod:
                if 'vUnCom' in child.tag:
                    vuncom = child
                    break
            unit_value = 0.0
            if vuncom is not None and vuncom.text:
                try:
                    unit_value = float(vuncom.text)
                except:
                    pass
            
            # Valor total do produto
            vprod = None
            for child in prod:
                if 'vProd' in child.tag:
                    vprod = child
                    break
            total_value = 0.0
            if vprod is not None and vprod.text:
                try:
                    total_value = float(vprod.text)
                except:
                    pass
            
            # Desconto (se houver)
            vdesc = None
            for child in prod:
                if 'vDesc' in child.tag:
                    vdesc = child
                    break
            if vdesc is not None and vdesc.text:
                try:
                    discount = float(vdesc.text)
                    total_value = max(0, total_value - discount)
                except:
                    pass
            
            # Categorizar o item
            category, subcategory = categorize_supermarket_item(description)
            
            return {
                'item_id': item_id,
                'description': description,
                'quantity': quantity,
                'unit_value': unit_value,
                'total_value': total_value,
                'category': category,
                'subcategory': subcategory
            }
            
        except Exception as e:
            print(f"Erro ao extrair informações do item: {e}")
            return None
    
    def parse_xml_text(self, xml_text: str, filename: str = None) -> Optional[SubTransactionXML]:
        """Parse XML a partir de texto"""
        try:
            root = ET.fromstring(xml_text)
            return self.parse_xml_content(root, filename)
        except Exception as e:
            print(f"Erro ao parsear XML a partir de texto: {e}")
            return None

def test_xml_parser():
    """Função para testar o parser com os XMLs de exemplo"""
    parser = NFeParser()
    
    # Testar com os XMLs de exemplo
    xml_files = ['xml/6585.xml', 'xml/8915.xml']
    
    for xml_file in xml_files:
        print(f"\n=== Testando {xml_file} ===")
        xml_obj = parser.parse_xml_file(xml_file)
        
        if xml_obj:
            print(f"XML ID: {xml_obj.xml_id}")
            print(f"Estabelecimento: {xml_obj.establishment_name}")
            print(f"Data: {xml_obj.emission_date}")
            print(f"Valor Total: R$ {xml_obj.total_value:.2f}")
            print(f"Total de itens: {xml_obj.get_total_items()}")
            
            # Mostrar resumo por categoria
            categories = xml_obj.get_categories_summary()
            print("\nResumo por categoria:")
            for category, value in categories.items():
                print(f"  {category}: R$ {value:.2f}")
            
            # Mostrar alguns itens
            print(f"\nPrimeiros 3 itens:")
            for i, item in enumerate(xml_obj.subtransactions[:3]):
                print(f"  {i+1}. {item.description} - R$ {item.total_value:.2f} ({item.category}/{item.subcategory})")
        else:
            print("Erro ao parsear XML")

if __name__ == "__main__":
    test_xml_parser()
