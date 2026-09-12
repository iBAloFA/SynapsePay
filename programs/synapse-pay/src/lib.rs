use anchor_lang::prelude::*;
use anchor_spl::token::{self, Token, TokenAccount, Transfer};
use solana_program::ed25519_program::ID as ED25519_ID;
use solana_program::sysvar::instructions as ix_sysvar;

declare_id!("5ACJCYjUkDKoUkuQjbaNjx6rpQY8XELiE7tyAg1NVffr"); // SolPG will auto-update this

#[program]
pub mod synapse_pay {
    use super::*;

    pub fn open_channel(
        ctx: Context<OpenChannel>,
        channel_id: u64,
        deposit_amount: u64,
        duration_slots: u64,
    ) -> Result<()> {
        let channel = &mut ctx.accounts.channel;
        channel.agent = ctx.accounts.agent.key();
        channel.provider = ctx.accounts.provider.key();
        channel.channel_id = channel_id;
        channel.deposited_amount = deposit_amount;
        channel.settled_amount = 0;
        channel.expires_at_slot = Clock::get()?.slot + duration_slots;
        channel.bump = ctx.bumps.channel;

        token::transfer(
            CpiContext::new(
                ctx.accounts.token_program.to_account_info(),
                Transfer {
                    from: ctx.accounts.agent_token_account.to_account_info(),
                    to: ctx.accounts.vault.to_account_info(),
                    authority: ctx.accounts.agent.to_account_info(),
                },
            ),
            deposit_amount,
        )?;

        Ok(())
    }

    pub fn close_and_settle(
        ctx: Context<CloseAndSettle>,
        final_amount: u64,
        _channel_nonce: u64,
    ) -> Result<()> {
        let channel = &ctx.accounts.channel;
        require!(final_amount <= channel.deposited_amount, ChannelError::ExceedsDeposit);

        let sysvar_info = &ctx.accounts.ix_sysvar;
        let current_ix_idx = ix_sysvar::load_current_index_checked(sysvar_info)?;
        require!(current_ix_idx > 0, ChannelError::MissingSignatureVerification);

        let ed25519_ix = ix_sysvar::load_instruction_at_checked((current_ix_idx - 1) as usize, sysvar_info)?;
        require_keys_eq!(ed25519_ix.program_id, ED25519_ID, ChannelError::InvalidPrecedingInstruction);

        let seeds = &[
            b"channel",
            channel.agent.as_ref(),
            channel.provider.as_ref(),
            &channel.channel_id.to_le_bytes(),
            &[channel.bump],
        ];
        let signer_seeds = &[&seeds[..]];

        if final_amount > 0 {
            token::transfer(
                CpiContext::new_with_signer(
                    ctx.accounts.token_program.to_account_info(),
                    Transfer {
                        from: ctx.accounts.vault.to_account_info(),
                        to: ctx.accounts.provider_token_account.to_account_info(),
                        authority: ctx.accounts.channel.to_account_info(),
                    },
                    signer_seeds,
                ),
                final_amount,
            )?;
        }

        let refund_amount = channel.deposited_amount.saturating_sub(final_amount);
        if refund_amount > 0 {
            token::transfer(
                CpiContext::new_with_signer(
                    ctx.accounts.token_program.to_account_info(),
                    Transfer {
                        from: ctx.accounts.vault.to_account_info(),
                        to: ctx.accounts.agent_token_account.to_account_info(),
                        authority: ctx.accounts.channel.to_account_info(),
                    },
                    signer_seeds,
                ),
                refund_amount,
            )?;
        }

        Ok(())
    }
}

#[account]
pub struct Channel {
    pub agent: Pubkey,
    pub provider: Pubkey,
    pub channel_id: u64,
    pub deposited_amount: u64,
    pub settled_amount: u64,
    pub expires_at_slot: u64,
    pub bump: u8,
}

#[derive(Accounts)]
#[instruction(channel_id: u64)]
pub struct OpenChannel<'info> {
    #[account(mut)]
    pub agent: Signer<'info>,
    /// CHECK: Recipient provider
    pub provider: AccountInfo<'info>,
    #[account(
        init,
        payer = agent,
        space = 8 + 32 + 32 + 8 + 8 + 8 + 8 + 1,
        seeds = [b"channel", agent.key().as_ref(), provider.key().as_ref(), &channel_id.to_le_bytes()],
        bump
    )]
    pub channel: Account<'info, Channel>,
    #[account(mut)]
    pub agent_token_account: Account<'info, TokenAccount>,
    #[account(
        init,
        payer = agent,
        token::mint = mint,
        token::authority = channel,
        seeds = [b"vault", channel.key().as_ref()],
        bump
    )]
    pub vault: Account<'info, TokenAccount>,
    pub mint: Account<'info, token::Mint>,
    pub token_program: Program<'info, Token>,
    pub system_program: Program<'info, System>,
    pub rent: Sysvar<'info, Rent>,
}

#[derive(Accounts)]
pub struct CloseAndSettle<'info> {
    #[account(
        mut,
        close = agent,
        seeds = [b"channel", channel.agent.as_ref(), channel.provider.as_ref(), &channel.channel_id.to_le_bytes()],
        bump = channel.bump
    )]
    pub channel: Account<'info, Channel>,
    /// CHECK: Refund account
    #[account(mut)]
    pub agent: AccountInfo<'info>,
    #[account(mut)]
    pub provider: Signer<'info>,
    #[account(mut)]
    pub vault: Account<'info, TokenAccount>,
    #[account(mut)]
    pub agent_token_account: Account<'info, TokenAccount>,
    #[account(mut)]
    pub provider_token_account: Account<'info, TokenAccount>,
    /// CHECK: Checked via ED25519 Instruction sysvar ID
    #[account(address = ix_sysvar::ID)]
    pub ix_sysvar: AccountInfo<'info>,
    pub token_program: Program<'info, Token>,
}

#[error_code]
pub enum ChannelError {
    #[msg("Settlement amount exceeds initial deposit.")]
    ExceedsDeposit,
    #[msg("Missing required preceding Ed25519 signature verification instruction.")]
    MissingSignatureVerification,
    #[msg("Instruction preceding close is not the Ed25519 native program.")]
    InvalidPrecedingInstruction,
}