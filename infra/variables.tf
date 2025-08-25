variable "aws_region" {
  type    = string
  default = "eu-west-1"
}

variable "project_name" {
  type    = string
  default = "churn-ml"
}

variable "instance_type" {
  type    = string
  default = "t3.small"
}

# Laisse vide si tu n'as pas de paire de clés EC2, ou mets le nom existant (ex: "my-keypair")
variable "key_name" {
  type    = string
  default = "churn-key"
}

# Qui peut se connecter en SSH (par défaut: tout le monde -> à restreindre !)
variable "allow_ssh_cidrs" {
  type    = list(string)
  default = ["0.0.0.0/0"]
}
