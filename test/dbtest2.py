from fido2.server import Fido2Server
from fido2.webauthn import PublicKeyCredentialRpEntity, PublicKeyCredentialUserEntity

# Укажите информацию о вашем сервере (RP — Relying Party)
rp = PublicKeyCredentialRpEntity(id="your-domain.com", name="Your Application")
server = Fido2Server(rp)

# Создайте данные пользователя
user = PublicKeyCredentialUserEntity(
    id=b"user-unique-id",  # Уникальный идентификатор пользователя
    name="username",
    display_name="User Display Name",
    icon="https://your-domain.com/user-icon.png",
)

# Шаг 1: Генерация опций для регистрации
registration_data = server.register_begin(
    user=user,
    user_verification="preferred",  # Требования к верификации
)

print("Отправьте эти данные на клиентскую сторону:", registration_data)

# Шаг 2: После получения ответа с клиента
client_data = b""  # Полученные данные от клиента (замените на реальные)
auth_data = b""    # Аутентификационные данные от клиента
signature = b""    # Подпись от клиента
attestation_object = b""  # Объект аттестации от клиента

# Завершение процесса регистрации
credentials = server.register_complete(
    registration_data["publicKey"],
    client_data,
    auth_data,
    attestation_object,
)

print("Регистрация завершена. Данные:", credentials)