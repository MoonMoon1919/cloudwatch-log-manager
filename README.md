# cloudwatch-log-manager

Created by M.Moon  

![](http://31.media.tumblr.com/9784bd9341d7bf57a258b6d287f8f3bc/tumblr_inline_nn40vfWblp1t7z78b_500.gif)  

A simple lambda for ensuring your CloudWatch logs don't get out of control. Because you shouldn't have to feel frantic about your monthly AWS spend. 

This lambda aims to:  
- Cleanup your CloudWatch log groups
- Lower your monthly AWS spend  
- Automate account maintenance  

---

## Why?

The cloud is cheap but that isn't an excuse to blow your yearly budget just to 'have something around'.  

Chances are you have a lot of underutilized logs sitting in Cloudwatch, this simple lambda runs on a schedule to ensure all log groups across any specified region in your account adhere to the same expiration policy.  

Without specification, CloudWatch Logs are set to expire after 10 years. If all of your infrastructure is in AWS and you're using CloudWatch Logs heavily (even if it's just a pitstop before you push your logs elsewhere) chances are you're paying quite a bit to store logs you aren't using. Your spend might be low now, but in 3 years you're going to be paying quite a bit just to house logs you don't care about anymore.

---

## How 

Pretty simple. The lambda runs on a schedule. I'd recommend once a week or once every two weeks.  

Setting up is easy just follow these steps:  
- Add your desired amount of days to store your logs and add the regions you have active logs in to /dist/local_config
- Run "python account_setup.py"
- Kick your feet up and worry about one less thing every day (alcoholic beverage optional)