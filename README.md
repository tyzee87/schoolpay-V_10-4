# SchoolPay V10.2

School fees management system with academic years, grade promotion, financial ledger, student 360, M-Pesa STK reconciliation, notifications, and PayBill C2B integration.

## PayBill / C2B
Parents can pay the school's PayBill using the student's **Pay Code as the M-Pesa Account Number**.

SchoolPay exposes:
- `POST /mpesa/c2b/validation`
- `POST /mpesa/c2b/confirmation`

In **M-Pesa / Daraja** settings, enter the public HTTPS URLs for those endpoints, save them, then click **Register PayBill C2B URLs**. The registration calls Safaricom Daraja's C2B Register URL API. The confirmation handler matches the `BillRefNumber`/Account Reference to an active student's pay code or ADM number. Unknown references go to **Unmatched Payments** rather than being credited to the wrong student.

## STK
STK Push remains available. Pending STK transactions are polled automatically and successful results are posted into the same payment ledger with duplicate protection.

## Important
For real PayBill callbacks, the validation and confirmation URLs must be reachable publicly over HTTPS. Termux on a phone by itself is normally not a stable public HTTPS server; use a proper hosted HTTPS endpoint for production callbacks.
