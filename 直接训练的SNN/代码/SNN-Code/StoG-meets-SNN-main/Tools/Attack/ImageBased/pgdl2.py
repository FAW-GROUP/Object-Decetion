import torch
from ...Attack.base import BaseAttack

EPS_FOR_DIVISION = 1e-12

class PGDL2(BaseAttack):
    def __init__(self, model, loss_function, forward_function=None, targeted=False, representation=None,
                 eps=0.3, alpha=2/255, steps=40, random_start=True, **kwargs):
        super(PGDL2, self).__init__(model, loss_function, forward_function, representation, targeted)
        self.eps = eps
        self.alpha = alpha
        self.steps = steps
        self.kwargs = kwargs
        self.random_start = random_start

    def forward(self, imgs, labels):
        imgs = imgs.clone().detach().to(imgs)
        labels = labels.clone().detach().to(imgs)
        adv_imgs = imgs.clone().detach()
        batch_size = len(imgs)

        if self.random_start:
            adv_imgs = adv_imgs + torch.empty_like(adv_imgs).uniform_(-self.eps, self.eps)
            adv_imgs = torch.clamp(adv_imgs, min=0, max=1).detach()

        for _ in range(self.steps):
            adv_imgs.requires_grad = True
            rpst = self.data_representation(adv_imgs)
            out = self.model_forward(rpst)
            loss = self.get_loss(out, labels)
            grad = torch.autograd.grad(loss, adv_imgs,
                                       retain_graph=False, create_graph=False)[0]
            
            grad_norms = torch.norm(grad.view(batch_size, -1), p=2, dim=1) + EPS_FOR_DIVISION
            grad = grad / grad_norms.view(batch_size, 1, 1, 1)
            adv_imgs = adv_imgs.detach() + self.alpha * grad
            delta = adv_imgs - imgs
            delta_norms = torch.norm(delta.view(batch_size, -1), p=2, dim=1)
            factor = self.eps / delta_norms
            factor = torch.min(factor, torch.ones_like(delta_norms))
            delta = delta * factor.view(-1, 1, 1, 1)
            adv_imgs = torch.clamp(imgs + delta, min=0, max=1).detach()
        return adv_imgs

