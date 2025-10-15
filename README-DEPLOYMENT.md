# Cartoon Animation Web - AI-Powered CI/CD Pipeline

This repository contains a complete CI/CD pipeline with AI integration for the Cartoon Animation Web application.

## 🚀 Features

- **AI-Powered Analysis**: OpenAI integration for PR analysis, test result interpretation, and deployment risk assessment
- **Automated Testing**: Unit tests with AI-generated summaries
- **Infrastructure as Code**: Terraform for AWS ECS/Fargate deployment
- **Automated Deployment**: Ansible playbooks for deployment and rollback
- **Real-time Monitoring**: CloudWatch integration with AI-powered anomaly detection
- **Auto-rollback**: Intelligent rollback based on AI analysis of metrics

## 📋 Prerequisites

1. **AWS Account** with appropriate permissions
2. **OpenAI API Key** for AI analysis
3. **GitHub Repository** with Actions enabled
4. **Docker** for local development

## 🛠️ Setup Instructions

### 1. Infrastructure Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd Cartoon-animation-web

# Set up AWS credentials
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

# Deploy infrastructure
cd terraform
terraform init
terraform plan
terraform apply
```

### 2. GitHub Secrets Configuration

Add these secrets to your GitHub repository:

```
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
OPENAI_API_KEY=your-openai-api-key
SLACK_WEBHOOK_URL=your-slack-webhook-url (optional)
```

### 3. ECR Repository Setup

```bash
# Get ECR login command
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push initial image
docker build -t cartoon-animation-web .
docker tag cartoon-animation-web:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/cartoon-animation-web:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/cartoon-animation-web:latest
```

## 🔄 CI/CD Pipeline Flow

### Stage 1: Code Commit & Build
- ✅ Code checkout and Docker image build
- ✅ Unit test execution
- 🤖 **AI Analysis**: PR change summary and risk assessment
- ✅ Docker image push to ECR

### Stage 2: Testing Stage
- ✅ Comprehensive test execution
- 🤖 **AI Analysis**: Test result interpretation and failure analysis
- ✅ Human-readable test summaries

### Stage 3: Pre-Deployment Validation
- ✅ Infrastructure readiness check (Terraform plan)
- ✅ ECR image verification
- 🤖 **AI Analysis**: Deployment risk assessment and strategy recommendation

### Stage 4: Deployment to ECS
- ✅ Ansible-based deployment to ECS Fargate
- ✅ Health check validation
- ✅ Load balancer configuration

### Stage 5: Post-Deployment Monitoring
- ✅ Real-time CloudWatch metrics collection
- 🤖 **AI Analysis**: Deployment summary and performance analysis
- ✅ Slack notification with deployment report

### Stage 6: Continuous Monitoring
- 🤖 **AI-Powered Anomaly Detection**: Real-time monitoring with automatic rollback
- ✅ Performance metrics tracking
- ✅ Error rate monitoring

## 🤖 AI Integration Features

### PR Analysis
- **Change Summary**: Concise description of modifications
- **Risk Assessment**: LOW/MEDIUM/HIGH risk classification
- **Risky Areas**: Specific code areas requiring attention
- **Testing Focus**: Recommended test areas

### Test Analysis
- **Failure Analysis**: Root cause analysis of test failures
- **Health Scoring**: 1-10 test health score
- **Recommendations**: Specific fix suggestions

### Deployment Risk Analysis
- **Strategy Recommendation**: CANARY vs FULL_ROLLOUT
- **Risk Mitigation**: Specific steps to reduce deployment risk
- **Monitoring Focus**: Key metrics to watch

### Real-time Monitoring
- **Anomaly Detection**: AI-powered detection of unusual patterns
- **Auto-rollback**: Automatic rollback for critical issues
- **Performance Analysis**: Continuous performance assessment

## 📊 Monitoring & Alerting

### CloudWatch Dashboard
- ECS service metrics (CPU, Memory)
- ALB request metrics and error rates
- Response time monitoring
- Target health status

### Alarms
- High CPU utilization (>80%)
- High memory utilization (>85%)
- High error rate (>10 errors)
- High response time (>2 seconds)
- Unhealthy targets

### AI-Powered Monitoring
- Real-time anomaly detection
- Automatic rollback triggers
- Performance trend analysis
- Predictive failure detection

## 🚨 Rollback Strategy

### Automatic Rollback Triggers
- Critical anomalies detected by AI
- Error rate exceeds threshold
- Response time degradation
- Memory/CPU spikes

### Manual Rollback
```bash
# Using Ansible
cd ansible
ansible-playbook -i inventory rollback.yml

# Using AWS CLI
aws ecs update-service --cluster cartoon-cluster --service cartoon-web-service --task-definition <previous-task-def>
```

## 🔧 Local Development

```bash
# Install dependencies
npm install

# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build

# Test Docker build
docker build -t cartoon-animation-web .
docker run -p 3000:80 cartoon-animation-web
```

## 📁 Project Structure

```
├── .github/workflows/          # GitHub Actions workflows
├── ansible/                    # Ansible deployment playbooks
├── terraform/                  # Infrastructure as Code
├── scripts/                    # AI analysis and monitoring scripts
├── src/                        # React application source
├── Dockerfile                  # Container configuration
├── nginx.conf                  # Nginx configuration
└── requirements.txt            # Python dependencies
```

## 🛡️ Security Features

- **Security Headers**: X-Frame-Options, X-Content-Type-Options, etc.
- **HTTPS Ready**: SSL certificate support
- **IAM Roles**: Least privilege access
- **VPC Security Groups**: Network isolation
- **Container Scanning**: ECR image vulnerability scanning

## 📈 Performance Optimizations

- **Multi-stage Docker Build**: Optimized image size
- **Nginx Caching**: Static asset caching
- **Gzip Compression**: Response compression
- **CDN Ready**: CloudFront integration support
- **Auto-scaling**: ECS service auto-scaling

## 🔍 Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Docker build logs
   - Verify ECR repository access
   - Ensure all dependencies are installed

2. **Deployment Failures**
   - Check ECS service logs
   - Verify task definition
   - Check ALB target group health

3. **AI Analysis Failures**
   - Verify OpenAI API key
   - Check API rate limits
   - Review error logs

### Debug Commands

```bash
# Check ECS service status
aws ecs describe-services --cluster cartoon-cluster --services cartoon-web-service

# View CloudWatch logs
aws logs tail /aws/ecs/cartoon-animation-web --follow

# Check ALB health
aws elbv2 describe-target-health --target-group-arn <target-group-arn>

# Run health checks
python3 scripts/health_check.py http://your-alb-dns-name
```

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review CloudWatch logs
3. Check GitHub Actions logs
4. Create an issue in the repository

## 🎯 Next Steps

- [ ] Add SSL certificate automation
- [ ] Implement blue-green deployments
- [ ] Add database integration
- [ ] Implement feature flags
- [ ] Add performance testing
- [ ] Set up log aggregation
- [ ] Add security scanning
- [ ] Implement cost optimization
