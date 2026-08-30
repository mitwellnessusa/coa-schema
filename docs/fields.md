# Field reference

Generated from `schema/coa.schema.json`. JSON Schema draft 2020-12.

Every object is `additionalProperties: false` — an unrecognised key is an error, 
which keeps transcription mistakes from passing silently.


## `schema_version`

Version of this schema the document was written against.

| Field | Type | | Description | Allowed values |
| --- | --- | --- | --- | --- |
| `schema_version` | string | **required** | Version of this schema the document was written against. |  |

## `document`

Identity and provenance of the certificate itself, as distinct from the product it describes.

| Field | Type | | Description | Allowed values |
| --- | --- | --- | --- | --- |
| `document` | object | **required** | Identity and provenance of the certificate itself, as distinct from the product it describes. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`document_id` | string | **required** | Identifier for this certificate, unique within the issuing laboratory. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`revision` | integer |  | Revision number. A reissued certificate increments this. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`date_issued` | string | **required** | Calendar date, ISO 8601, YYYY-MM-DD. Relative dates are not representable by design. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`supersedes` | string |  | document_id of the certificate this one replaces, if any. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`authorized_by` | object |  | Name and title of the person who released the certificate. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`name` | string | **required** |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`title` | string |  |  |  |

## `product`

The material tested. A certificate covers exactly one lot.

| Field | Type | | Description | Allowed values |
| --- | --- | --- | --- | --- |
| `product` | object | **required** | The material tested. A certificate covers exactly one lot. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`name` | string | **required** |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`lot_identifier` | string | **required** | The lot or batch code printed on the product. Without this the certificate cannot be matched to physical product, which is the single most common defect in published COAs. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`sku` | string |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`form` | string |  | Physical form of the tested material. | `powder`, `capsule`, `tablet`, `liquid`, `extract`, `tincture`, `softgel`, `gummy`, `raw_material`, `other` |
| &nbsp;&nbsp;&nbsp;&nbsp;`botanical_name` | string |  | Binomial name where the product is a botanical. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`manufacturer` | object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`name` | string | **required** |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`address` | string |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`identifier` | string |  | Registry identifier, e.g. an FDA establishment number. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`date_manufactured` | string |  | Calendar date, ISO 8601, YYYY-MM-DD. Relative dates are not representable by design. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`quantity_tested` | object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`value` | number | **required** |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`unit` | string | **required** |  |  |

## `laboratory`

The testing laboratory. An unnamed laboratory makes a certificate unverifiable.

| Field | Type | | Description | Allowed values |
| --- | --- | --- | --- | --- |
| `laboratory` | object | **required** | The testing laboratory. An unnamed laboratory makes a certificate unverifiable. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`name` | string | **required** |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`address` | string |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`accreditation` | array |  | Accreditation held by the laboratory, e.g. ISO/IEC 17025:2017. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`independent` | boolean |  | True when the laboratory is not owned by or affiliated with the manufacturer. Omit rather than guess. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`contact` | string |  |  |  |

## `sampling`

| Field | Type | | Description | Allowed values |
| --- | --- | --- | --- | --- |
| `sampling` | object |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`date_received` | string |  | Calendar date, ISO 8601, YYYY-MM-DD. Relative dates are not representable by design. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`date_tested` | string |  | Calendar date, ISO 8601, YYYY-MM-DD. Relative dates are not representable by design. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`sampled_by` | string |  |  | `laboratory`, `client`, `third_party`, `unknown` |
| &nbsp;&nbsp;&nbsp;&nbsp;`condition_on_receipt` | string |  |  |  |

## `results`

One entry per analyte measured. An empty array is not a certificate.

| Field | Type | | Description | Allowed values |
| --- | --- | --- | --- | --- |
| `results` | array | **required** | One entry per analyte measured. An empty array is not a certificate. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`analyte` | string | **required** | Substance measured, e.g. 'Lead', 'Mitragynine', 'Total aerobic microbial count'. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`panel` | string | **required** | Which test panel this result belongs to. | `potency`, `heavy_metals`, `microbial`, `pesticides`, `residual_solvents`, `mycotoxins`, `moisture`, `identity`, `other` |
| &nbsp;&nbsp;&nbsp;&nbsp;`method` | string | **required** | Analytical method, e.g. 'ICP-MS', 'HPLC-UV', 'USP <2021>'. A result without a method cannot be compared to another laboratory's result. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`value` | number |  | Numeric result. Omit when the result is non-numeric or below the limit of quantitation; use value_qualifier instead. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`value_qualifier` | string |  | Used when a numeric value is not the correct representation. | `below_loq`, `below_lod`, `not_detected`, `detected`, `pass`, `fail`, `not_tested` |
| &nbsp;&nbsp;&nbsp;&nbsp;`unit` | string |  | Unit of measure. ppm and mg/kg are equivalent; ppb is one thousandth of ppm, and confusing the two is a 1000x error that appears in real certificates. | `mg/kg`, `ug/kg`, `mg/g`, `ug/g`, `ppm`, `ppb`, `percent`, `mg/mL`, `mg/serving`, `CFU/g`, `MPN/g`, `cfu/mL`, `count`, `unitless` |
| &nbsp;&nbsp;&nbsp;&nbsp;`limit_of_quantitation` | number |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`limit_of_detection` | number |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`specification` | object |  | The acceptance criterion this result was judged against. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`operator` | string |  |  | `<=`, `<`, `>=`, `>`, `==`, `absent_in`, `range` |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`value` | number |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`min` | number |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`max` | number |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`unit` | string |  | Unit of measure. ppm and mg/kg are equivalent; ppb is one thousandth of ppm, and confusing the two is a 1000x error that appears in real certificates. | `mg/kg`, `ug/kg`, `mg/g`, `ug/g`, `ppm`, `ppb`, `percent`, `mg/mL`, `mg/serving`, `CFU/g`, `MPN/g`, `cfu/mL`, `count`, `unitless` |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`source` | string |  | Where the criterion comes from, e.g. 'USP', 'AHPA', 'internal'. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`outcome` | string |  | The laboratory's stated judgement. Validated against specification and value by the consistency rules, which is where most real defects surface. | `pass`, `fail`, `not_applicable`, `informational` |

## `notes`

| Field | Type | | Description | Allowed values |
| --- | --- | --- | --- | --- |
| `notes` | string |  |  |  |

## `source`

Where this record was transcribed from.

| Field | Type | | Description | Allowed values |
| --- | --- | --- | --- | --- |
| `source` | object |  | Where this record was transcribed from. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`url` | string |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`retrieved` | string |  | Calendar date, ISO 8601, YYYY-MM-DD. Relative dates are not representable by design. |  |
| &nbsp;&nbsp;&nbsp;&nbsp;`transcribed_by` | string |  |  |  |
