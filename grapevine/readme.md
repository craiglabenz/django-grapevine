### MailMan

The MailMan is a job that can be run repeatedly and will queue up messages for sending. It's logical flow is as follows:

1. Loop over all `ContentTypes`, finding models are a subclass of `SendableMixin`.
1. For each such `ContentType`, it loops over messages meeting the following criteria:
    * Unsent - The Sendable's `message_id` pointer is NULL
    * Ready to Send - The Sendable's `scheduled_send_time` is <= `NOW`
    * Unqueued - The message is not currently queued for imminent delivery
    * Sendable - A custom set of artibrary logic provided by the Sendable.
1. Each Sendable object pulled out of that loop calls `final_send_check()`, which should return a Boolean, where True means sending is OK and False means the message must remain unsent. This is a logical override point for each Sendable model based on its unique business requirements. Note that when this function returns False, it is also encouraged to alter `self.scheduled_send_time`, or the MailMan will immediately consider it again on the next pass.
1. Still-eligible Sendable objects are passed to the `SENDER_CLASS` as per the settings definition, which either sends the message immediately (and synchronously) or queues the message for near-immediate delivery.
    * Queued messages are registered as being such to prevent repeated queuing.
