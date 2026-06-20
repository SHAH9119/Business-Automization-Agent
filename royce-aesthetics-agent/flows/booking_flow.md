# Booking Flow

Goal: convert interested visitors into appointment requests without pretending the appointment is confirmed unless a real calendar/staff confirmation exists.

## Step 1: Understand Intent

Detect if the user wants:

- Appointment
- Price
- Service information
- Doctor availability
- Location
- Timing
- Human staff
- Urgent help

## Step 2: Collect Required Fields

Collect:

- Full name
- Phone number
- Main concern or service
- Preferred day
- Preferred time window
- Preferred language

Optional:

- New or returning patient
- Age range
- Any urgency

## Step 3: Offer Time Windows

Because public timing is 12 PM to 5 PM, offer broad windows first:

- 12 PM - 2 PM
- 2 PM - 4 PM
- 4 PM - 5 PM

Do not confirm exact availability unless connected to a real calendar.

## Step 4: Create Demo Booking

For the first demo, save the request in your database and optionally create it in your own demo Google Calendar.

Calendar event title:

`Demo appointment request - {name} - {service_or_concern}`

Calendar description:

`Phone: {phone}
Concern: {concern}
Preferred time: {preferred_time}
Source: Website/SMS/WhatsApp demo agent`

## Step 5: Confirmation Message

Use this wording:

"Thank you, {name}. I have noted your appointment request for {concern} around {preferred_time}. A staff member can confirm the exact slot. If this is urgent, please call 0335-6377775 directly."

