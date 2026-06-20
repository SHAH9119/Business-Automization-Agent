# Human Handoff Flow

The assistant should hand off when:

- The user asks for a doctor or human.
- The user asks for diagnosis or treatment recommendation.
- The user shares urgent symptoms.
- The user is angry or confused.
- The assistant cannot answer from the knowledge base.
- The user asks for price confirmation and no verified price exists.
- The user wants a confirmed appointment slot but no live calendar is connected.

## Staff Alert Format

Send this to staff/demo owner:

`New AI receptionist handoff
Name: {name}
Phone: {phone}
Concern: {concern}
Preferred time: {preferred_time}
Reason for handoff: {handoff_reason}
Conversation summary: {summary}`

## User Message

"I will forward this to the clinic team so they can guide you properly. Please call 0335-6377775 directly if this is urgent."

