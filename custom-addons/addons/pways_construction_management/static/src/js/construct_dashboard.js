odoo.define("pways_construction_management.constructdashboard", function (require) {
   "use strict";

    console.log(".....pways_construction_management.constructdashboard.....")
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var ajax = require('web.ajax');
    const _t = core._t;

    var session = require('web.session');
    var current_user_id = session.user_id

    var ConstructionDashboard = AbstractAction.extend({
        contentTemplate: 'ConstructionDashboard',

        events: {
            'click .job_costing': 'view_job_costing',
            'click .projects': 'view_projects',
            'click .tasks': 'view_tasks',
            'click .contractors': 'view_contractors',
            'click .bills': 'view_bills',
            'click .picking': 'view_picking',
            'click .inspection ': 'view_inspection',
            'click .compliance ': 'view_compliance',
            'click .material ': 'view_material',
            'click .purchase_requisition ': 'view_purchase_requisition',
            'click .internal_requisition ': 'view_internal_requisition',
            'click .scrap_requisition ': 'view_scrap_requisition',
        },

        renderElement: function (ev) {
            const self = this;
            this.willStart();
            $.when(this._super())
            .then(function (ev) {
                rpc.query({
                    model: "res.partner",
                    method: "get_farm_stats",
                }).then(function (result) {
                    $('#job_costing_count').empty().append(result['job_costing_count']);
                    $('#projects_count').empty().append(result['projects_count']);
                    $('#tasks_count').empty().append(result['tasks_count']);
                    $('#contractors_count').empty().append(result['contractors_count']);
                    $('#bills_count').empty().append(result['bills_count']);
                    $('#picking_count').empty().append(result['picking_count']);
                    $('#inspection_count').empty().append(result['inspection_count']);
                    $('#compliance_count').empty().append(result['compliance_count']);
                    $('#materials_count').empty().append(result['materials_count']);
                    $('#purchase_count').empty().append(result['purchase_count']);
                    $('#in_picking_count').empty().append(result['in_picking_count']);
                    $('#scraps_count').empty().append(result['scraps_count']);
                });
            });
        },

        view_job_costing: function (ev) {
            ev.preventDefault();
            return this.do_action({
                name: _t('All Cost Sheets'),
                type: 'ir.actions.act_window',
                res_model: 'job.costing',
                domain: [['user_id', '=', current_user_id]],
                views: [[false, 'list'], [false, 'form']],
                target: 'current'
            });
        },

        view_projects: function (ev) {
            ev.preventDefault();
            return this.do_action({
                name: _t('All Projects'),
                type: 'ir.actions.act_window',
                res_model: 'project.project',
                domain: [['user_id', '=', current_user_id]],
                views: [[false, 'list'], [false, 'form']],
                target: 'current'
            });
        },

        view_tasks: function (ev) {
            ev.preventDefault();
            return this.do_action({
                name: _t('All Tasks'),
                type: 'ir.actions.act_window',
                res_model: 'project.task',
                domain: [['project_id', '!=', false],['user_ids', 'in', current_user_id]],
                views: [[false, 'list'], [false, 'form']],
                target: 'current'
            });
        },

        view_contractors: function (ev) {
            ev.preventDefault();
            return this.do_action({
                name: _t('All Contractors'),
                type: 'ir.actions.act_window',
                res_model: 'res.partner',
                // domain: [[]],
                views: [[false, 'list'], [false, 'form']],
                target: 'current'
            });
        },

        view_bills: function (ev) {
            ev.preventDefault();
            return this.do_action({
                name: _t('All Bills'),
                type: 'ir.actions.act_window',
                res_model: 'account.move',
                domain: ['|', '|', ['project_id', '!=', false], ['task_id', '!=', false], ['job_cost_id', '!=', false]],
                views: [[false, 'list'], [false, 'form']],
                target: 'current'
            });
        },

        view_picking: function (ev) {
            ev.preventDefault();
            return this.do_action({
                name: _t('All Pickings'),
                type: 'ir.actions.act_window',
                res_model: 'stock.picking',
                domain: ['|', '|', ['project_id', '!=', false], ['task_id', '!=', false], ['job_cost_id', '!=', false]],
                views: [[false, 'list'], [false, 'form']],
                target: 'current'
            });
        },

        view_inspection: function (ev) {
            ev.preventDefault();
            return this.do_action({
                name: _t('All Inspections'),
                type: 'ir.actions.act_window',
                res_model: 'construct.inspector',
                domain: [['inspector_id', '=', current_user_id]],
                views: [[false, 'list'], [false, 'form']],
                target: 'current'
            });
        },

        view_compliance: function (ev) {
            ev.preventDefault();
            return this.do_action({
                name: _t('All Compliance'),
                type: 'ir.actions.act_window',
                res_model: 'construct.compliance',
                // domain: [['user_id', '=', current_user_id]],
                views: [[false, 'list'], [false, 'form']],
                target: 'current'
            });
        },

        view_material: function (ev) {
            ev.preventDefault();
            return this.do_action({
                name: _t('All Materials'),
                type: 'ir.actions.act_window',
                res_model: 'product.product',
                views: [[false, 'list'], [false, 'form']],
                target: 'current'
            });
        },

        view_purchase_requisition: function (ev) {
            ev.preventDefault();
            return this.do_action({
                name: _t('All Purchase'),
                type: 'ir.actions.act_window',
                res_model: 'material.purchase.requisition',
                domain: [['requisition_type', '=', 'purchase'], ['task_user_ids', 'in', current_user_id]],
                views: [[false, 'list'], [false, 'form']],
                target: 'current'
            });
        },

        view_internal_requisition: function (ev) {
            ev.preventDefault();
            return this.do_action({
                name: _t('All Purchase'),
                type: 'ir.actions.act_window',
                res_model: 'material.purchase.requisition',
                domain: [['requisition_type', '=', 'internal'], ['task_user_ids', 'in', current_user_id]],
                views: [[false, 'list'], [false, 'form']],
                target: 'current'
            });
        },
        
        view_scrap_requisition: function (ev) {
            ev.preventDefault();
            return this.do_action({
                name: _t('All Purchase'),
                type: 'ir.actions.act_window',
                res_model: 'material.purchase.requisition',
                domain: [['requisition_type', '=', 'scrap'], ['task_user_ids', 'in', current_user_id]],
                views: [[false, 'list'], [false, 'form']],
                target: 'current'
            });
        },

        ConstructManagementDashboard: {},

        willStart: function() {
            var self = this;

            // Load Google Charts and data simultaneously
            var dashboardPromise = ajax.rpc('/construct/dashboard', {})
                .then(function (result) {
                    self.ConstructManagementDashboard = result;
                    return result;
                });

            var googleChartsPromise = new Promise(function (resolve, reject) {
                google.charts.load('current', {'packages': ['corechart', 'bar']});
                google.charts.setOnLoadCallback(function () {
                    resolve();
                });
            });

            // Wait for both data and Google Charts to be ready
            return Promise.all([this._super.apply(this, arguments), dashboardPromise, googleChartsPromise])
                .then(function (results) {
                    var result = results[1]; // Dashboard data from RPC
                    self.drawCharts(result);
                });
        },

        drawCharts: function (result) {
            try {
                // Project Pie chart
                var project_data = google.visualization.arrayToDataTable(result['project_state_data']);
                var project_options = {
                    'backgroundColor': 'transparent',
                    pieHole: 0.4
                };
                var project_chart = new google.visualization.PieChart(document.getElementById('project_state_chart'));
                project_chart.draw(project_data, project_options);

                // Task Pie chart
                var task_data = google.visualization.arrayToDataTable(result['task_stage_data']);
                var task_options = {
                    'backgroundColor': 'transparent',
                    is3D: true
                };
                var task_chart = new google.visualization.PieChart(document.getElementById('task_stage_chart'));
                task_chart.draw(task_data, task_options);

                // Yearly Invoices Line Chart
                var invoice_data = google.visualization.arrayToDataTable(result['project_invocie_yearly']);
                var invoice_options = {
                    'backgroundColor': 'transparent',
                    hAxis: {title: 'Month'},
                    vAxis: {title: 'Total Invoices'},
                    legend: 'none',
                    bar: {groupWidth: "75%"}
                };
                var invoice_chart = new google.visualization.ColumnChart(document.getElementById('project_invocie_yearly'));
                invoice_chart.draw(invoice_data, invoice_options);
                
                //Cost Type Wise Estimented Amount Column chart
                var column_data = google.visualization.arrayToDataTable(result['cost_type_estimated_amount_yearly']);
                var column_options = {
                    'backgroundColor': 'transparent',
                    legend: 'none',
                    bar: {
                        groupWidth: "40%"
                    },
                };
                var column_chart = new google.visualization.ColumnChart(document.getElementById('cost_type_estimated_amount_yearly'));
                column_chart.draw(column_data, column_options);

            } catch (e) {
                console.error("Error drawing charts", e);
            }
        },

    });
    
   core.action_registry.add('construct_dashboard', ConstructionDashboard);
   return ConstructionDashboard;
});