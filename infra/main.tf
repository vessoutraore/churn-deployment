# AMI Amazon Linux 2023
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["137112412989"] # Amazon

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_security_group" "churn_sg" {
  name        = "${var.project_name}-sg"
  description = "Allow SSH, HTTP, 8000, 8501"
  vpc_id      = null # default VPC

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allow_ssh_cidrs
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "FastAPI 8000"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Streamlit 8501"
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-sg"
  }
}

# Script de bootstrap: installe Docker et lance tes conteneurs (à adapter à tes images)
locals {
  user_data = <<-EOF
    #!/bin/bash
    set -e

    # MAJ + Docker
    dnf update -y
    dnf install -y docker
    systemctl enable docker
    systemctl start docker
    usermod -aG docker ec2-user

    # (Option) ECR login ou Docker Hub si images publiques
    # docker login -u <user> -p <password>

    # Récupère et lance l'API FastAPI (adapte le nom de l'image)
    docker pull vessou/churn-api:latest || true
    docker rm -f churn-api || true
    docker run -d --name churn-api -p 8000:8000 vessou/churn-api:latest

    # Récupère et lance l'app Streamlit (adapte le nom de l'image)
    docker pull vessou/churn-app:latest || true
    docker rm -f churn-app || true
    docker run -d --name churn-app -p 8501:8501 vessou/churn-app:latest
  EOF
}

resource "aws_instance" "churn" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.churn_sg.id]
  user_data              = local.user_data

  tags = {
    Name = "${var.project_name}-ec2"
  }
}
