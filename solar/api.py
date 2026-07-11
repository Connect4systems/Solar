import frappe


@frappe.whitelist()
def make_sales_order_with_solar_items(source_name, target_doc=None):
	"""Create Sales Order and append Quotation custom_solar rows when needed."""
	from erpnext.selling.doctype.quotation.quotation import (
		make_sales_order as core_make_sales_order,
	)

	sales_order = core_make_sales_order(source_name, target_doc=target_doc)
	quotation = frappe.get_doc("Quotation", source_name)

	if quotation.get("custom_type") != "Solar & Wells":
		return sales_order

	_append_custom_solar_items(quotation, sales_order)

	sales_order.flags.ignore_permissions = True
	sales_order.run_method("set_missing_values")
	sales_order.run_method("calculate_taxes_and_totals")

	return sales_order


def _append_custom_solar_items(quotation, sales_order):
	quotation_item_fields = _copyable_fieldnames("Quotation Item")
	sales_order_item_fields = _copyable_fieldnames("Sales Order Item")
	shared_fields = quotation_item_fields & sales_order_item_fields

	for quotation_item in quotation.get("custom_solar") or []:
		if not quotation_item.get("item_code"):
			continue

		row = {
			fieldname: quotation_item.get(fieldname)
			for fieldname in shared_fields
			if quotation_item.get(fieldname) not in (None, "")
		}

		if "quotation" in sales_order_item_fields:
			row["quotation"] = quotation.name
		if "quotation_item" in sales_order_item_fields:
			row["quotation_item"] = quotation_item.name

		sales_order.append("items", row)


def _copyable_fieldnames(doctype):
	excluded_fields = {
		"name",
		"owner",
		"creation",
		"modified",
		"modified_by",
		"docstatus",
		"idx",
		"parent",
		"parentfield",
		"parenttype",
	}

	return {
		df.fieldname
		for df in frappe.get_meta(doctype).fields
		if df.fieldname and df.fieldname not in excluded_fields and not df.get("no_copy")
	}
