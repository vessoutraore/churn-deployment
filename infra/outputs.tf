output "public_ip" { value = aws_instance.churn.public_ip }
output "app_url"   { value = "http://${aws_instance.churn.public_ip}/" }
output "api_url"   { value = "http://${aws_instance.churn.public_ip}/api" }
