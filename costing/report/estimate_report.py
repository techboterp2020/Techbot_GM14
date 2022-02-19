from odoo import api, fields, models, _

class Lab_report(models.AbstractModel):
    _name = 'report.costing.report_estimate_template'
    _description = 'Estimate Reports'

    @api.model
    def _get_report_values(self, docids, data):
        print(self.id,"$$$$$$$$$$$")
        print('DOIds',docids)
        print('FATA',data)

        val_test = {}
        test_list = []
        val_parameter = {}
        parameter_list = []

        docs = self.env['product.costing'].browse(docids[0])
        print(docids[0],"%%%%%%%%%%%%%")
        product_recieve_line = self.env['product.estimate.lines'].search([('costing_id','=',docids[0])])
        for prod in product_recieve_line:
            print(prod.name.name,"$$$$$$$$$$")
            assign_tests = self.env['product.bom.lines'].search([('product_bom_id','=',prod.id)])
            for test in assign_tests:
                print(test.proposed_cost,"TTTTTTTeeesssss")
                val_test = {
                    'receipts_assigned_lines' : prod.id,
                    'product_id' : prod.name.name,
                }
                test_list.append(val_test)

                val_parameter = {
                    'product_bom_id':prod.id,
                    'product_id': test.product_id.name,
                    'prod_length': test.prod_length,
                    'prod_breadth': test.prod_breadth,
                    'qty': test.qty,
                    'uom_id': test.uom_id.name
                }
                parameter_list.append(val_parameter)

        print(parameter_list, "*************************************************************************")
        print(test_list, "PPPPPPPPPPPPPRRRRRRRRRRRRRRRRRRRRR")

        return {
            'doc_model': 'sample.receipts',
            'data': data,
            'docs': docs,
            'test_list': test_list,
            'parameter_list': parameter_list,
        }
